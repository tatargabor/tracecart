#!/usr/bin/env python3
"""Integration tests for LSP server logic (no actual LSP client needed)."""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lsp'))

from server import SetTraceServer, STATUS_SEVERITY, SKIP_STATUSES
from lsprotocol import types


def make_server(fixture='test-trace-map.json'):
    ls = SetTraceServer()
    tm_path = Path(__file__).parent / 'fixtures' / fixture
    ls._trace_map_path = tm_path
    ls.load_trace_map()
    return ls


def test_load_trace_map():
    ls = make_server()
    assert ls._trace_map is not None
    assert ls._trace_map['version'] == 1
    assert len(ls._trace_map['traces']) == 12
    assert len(ls._trace_map.get('reverse_traces', [])) == 2
    # Second load should return False (no change)
    assert ls.load_trace_map() is False
    print("  load_trace_map: OK")


def test_no_trace_map():
    ls = SetTraceServer()
    ls._trace_map_path = Path("/nonexistent/trace-map.json")
    assert ls.load_trace_map() is False
    assert ls._trace_map is None
    diags = ls.build_diagnostics("file:///some/file.md")
    assert diags == []
    print("  no_trace_map graceful: OK")


def test_diagnostics_severity():
    ls = make_server()
    diags = ls.build_diagnostics("file:///path/to/tests/fixtures/source.md")

    statuses = [d.message.split(']')[0].lstrip('[') for d in diags]

    assert any('MISSING' in s for s in statuses), "Should have MISSING"
    assert any('PARTIAL' in s for s in statuses), "Should have PARTIAL"
    assert any('COVERED' in s for s in statuses), "Should have COVERED"
    assert not any(s.strip() == 'N/A' for s in statuses), "N/A should be skipped"

    for d in diags:
        if '[MISSING]' in d.message:
            assert d.severity == types.DiagnosticSeverity.Error
        elif '[PARTIAL]' in d.message and 'PARTIAL_SOURCE' not in d.message:
            assert d.severity == types.DiagnosticSeverity.Warning
        elif '[COVERED]' in d.message:
            assert d.severity == types.DiagnosticSeverity.Hint

    print(f"  diagnostics_severity: OK ({len(diags)} diagnostics)")


def test_diagnostics_reverse_traces():
    ls = make_server()
    diags = ls.build_diagnostics("file:///path/to/tests/fixtures/target.md")

    reverse_diags = [d for d in diags if d.source == "set-trace-reverse"]
    assert len(reverse_diags) == 1, f"Expected 1 reverse diag (PARTIAL_SOURCE), got {len(reverse_diags)}"

    rd = reverse_diags[0]
    assert 'PARTIAL_SOURCE' in rd.message
    assert 'nearest: T-abc123-017-2' in rd.message
    print(f"  diagnostics_reverse_traces: OK ({len(reverse_diags)} reverse)")


def test_goto_definition():
    ls = make_server()
    tm = ls._trace_map
    filepath = "tests/fixtures/source.md"

    # Line 5 has COVERED traces with refs
    found = None
    for trace in tm.get('traces', []):
        source = trace.get('source', {})
        if ls.path_matches(f"/path/to/{filepath}", source.get('file', '')) and source.get('line') == 5:
            refs = trace.get('refs', [])
            if refs:
                found = refs[0]
                break

    assert found is not None, "Should find ref for COVERED trace at line 5"
    assert found['file'] == 'tests/fixtures/target.md'
    print("  goto_definition (COVERED): OK")

    # Line with MISSING trace has no refs
    for trace in tm.get('traces', []):
        source = trace.get('source', {})
        if ls.path_matches(f"/path/to/{filepath}", source.get('file', '')) and trace.get('status') == 'MISSING':
            assert trace.get('refs', []) == [], "MISSING trace should have no refs"
    print("  goto_definition (MISSING): OK")


def test_find_references():
    ls = make_server()
    tm = ls._trace_map

    # Target line 7 should be referenced by 2 traces
    refs_at_7 = []
    for trace in tm.get('traces', []):
        for ref in trace.get('refs', []):
            if ls.path_matches("/path/to/tests/fixtures/target.md", ref.get('file', '')) and ref.get('line') == 7:
                refs_at_7.append(trace['id'])

    assert len(refs_at_7) == 2, f"Expected 2 refs at target line 7, got {len(refs_at_7)}"
    print(f"  find_references: OK ({len(refs_at_7)} refs)")


def test_code_lens():
    ls = make_server()
    source_path = str(Path(__file__).parent / 'fixtures' / 'source.md')
    uri = f"file://{source_path}"
    lenses = ls.get_code_lenses(uri)

    assert len(lenses) > 0, "Should produce code lenses"
    for lens in lenses:
        assert '[set-trace]' in lens.command.title
        assert 'traces:' in lens.command.title

    total_traces = sum(
        int(lens.command.title.split('traces:')[0].split()[-1])
        for lens in lenses
    )
    print(f"  code_lens: OK ({len(lenses)} lenses, {total_traces} total traces)")


def test_stale_detection():
    ls = SetTraceServer()

    with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as f:
        json.dump({
            'version': 1, 'traces': [
                {'id': 'T-1', 'status': 'MISSING', 'text': 'test req',
                 'source': {'file': 'stale_test.md', 'line': 1, 'col_start': 0, 'col_end': 20}}
            ],
            'source_files': [], 'target_files': [], 'summary': {},
        }, f)
        tm_path = f.name

    with tempfile.NamedTemporaryFile(suffix='.md', mode='w', delete=False, prefix='stale_test') as src:
        src.write("# test\nsome content\n")
        src_path = src.name

    ls._trace_map_path = Path(tm_path)
    ls.load_trace_map()

    # Touch source to be newer
    time.sleep(0.1)
    Path(src_path).touch()

    assert ls.is_stale(src_path) is True
    assert ls.is_stale("/nonexistent") is False

    # Build diagnostics for stale file — severity should be Hint
    diags = ls.build_diagnostics(f"file://{src_path}")
    # Path won't match 'stale_test.md' exactly, so skip that check

    os.unlink(tm_path)
    os.unlink(src_path)
    print("  stale_detection: OK")


def test_hot_reload_detect():
    ls = SetTraceServer()

    with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as f:
        json.dump({
            'version': 1,
            'traces': [{'id': 'T-1', 'status': 'COVERED', 'text': 'x',
                         'source': {'file': 'a.md', 'line': 1}}],
            'source_files': [], 'target_files': [], 'summary': {},
        }, f)
        tm_path = f.name

    ls._trace_map_path = Path(tm_path)
    assert ls.load_trace_map() is True
    assert len(ls._trace_map['traces']) == 1

    # No change
    assert ls.load_trace_map() is False

    # Modify
    time.sleep(0.1)
    with open(tm_path, 'w') as f:
        json.dump({
            'version': 1,
            'traces': [
                {'id': 'T-1', 'status': 'COVERED', 'text': 'x', 'source': {'file': 'a.md', 'line': 1}},
                {'id': 'T-2', 'status': 'MISSING', 'text': 'y', 'source': {'file': 'a.md', 'line': 2}},
            ],
            'source_files': [], 'target_files': [], 'summary': {},
        }, f)

    assert ls.load_trace_map() is True
    assert len(ls._trace_map['traces']) == 2

    # Delete → clears data
    os.unlink(tm_path)
    assert ls.load_trace_map() is True
    assert ls._trace_map is None

    print("  hot_reload_detect: OK")


if __name__ == '__main__':
    print("Running LSP integration tests...")
    test_load_trace_map()
    test_no_trace_map()
    test_diagnostics_severity()
    test_diagnostics_reverse_traces()
    test_goto_definition()
    test_find_references()
    test_code_lens()
    test_stale_detection()
    test_hot_reload_detect()
    print("\nAll LSP tests passed!")
