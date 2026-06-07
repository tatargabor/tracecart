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

FIXTURES = Path(__file__).parent / 'fixtures'


def make_server(fixture_dir='test1'):
    ls = SetTraceServer()
    tm_path = FIXTURES / fixture_dir / 'trace-map.json'
    ls._trace_map_paths = [tm_path]
    ls._trace_map_mtimes = {str(tm_path): tm_path.stat().st_mtime}
    ls._trace_map = json.loads(tm_path.read_text(encoding='utf-8'))
    return ls


def make_multi_server():
    """Load test1 + test2 trace-maps together, simulating multi-trace discovery."""
    ls = SetTraceServer()
    paths = [
        FIXTURES / 'test1' / 'trace-map.json',
        FIXTURES / 'test2' / 'trace-map.json',
    ]
    ls._trace_map_paths = paths
    ls._trace_map_mtimes = {str(p): p.stat().st_mtime for p in paths}
    merged = {'traces': [], 'reverse_traces': []}
    for p in paths:
        data = json.loads(p.read_text(encoding='utf-8'))
        merged['traces'].extend(data.get('traces', []))
        merged['reverse_traces'].extend(data.get('reverse_traces', []))
    ls._trace_map = merged
    return ls


# --- test1: single source, single target, single trace-map ---

def test_load_trace_map():
    ls = make_server('test1')
    assert ls._trace_map is not None
    assert ls._trace_map['version'] == 1
    assert len(ls._trace_map['traces']) == 12
    assert len(ls._trace_map.get('reverse_traces', [])) == 2
    print("  test1/load_trace_map: OK")


def test_no_trace_map():
    ls = SetTraceServer()
    assert ls._trace_map is None
    diags = ls.build_diagnostics("file:///some/file.md")
    assert diags == []
    print("  test1/no_trace_map graceful: OK")


def test_diagnostics_severity():
    ls = make_server('test1')
    diags = ls.build_diagnostics("file:///path/to/tests/fixtures/test1/source.md")

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

    print(f"  test1/diagnostics_severity: OK ({len(diags)} diagnostics)")


def test_diagnostics_reverse_traces():
    ls = make_server('test1')
    diags = ls.build_diagnostics("file:///path/to/tests/fixtures/test1/target.md")

    reverse_diags = [d for d in diags if d.source == "set-trace-reverse"]
    assert len(reverse_diags) == 1, f"Expected 1 reverse diag (PARTIAL_SOURCE), got {len(reverse_diags)}"

    rd = reverse_diags[0]
    assert 'PARTIAL_SOURCE' in rd.message
    assert 'nearest: T-abc123-017-2' in rd.message
    print(f"  test1/diagnostics_reverse_traces: OK ({len(reverse_diags)} reverse)")


def test_goto_definition():
    ls = make_server('test1')
    tm = ls._trace_map
    filepath = "tests/fixtures/test1/source.md"

    found = None
    for trace in tm.get('traces', []):
        source = trace.get('source', {})
        if ls.path_matches(f"/path/to/{filepath}", source.get('file', '')) and source.get('line') == 5:
            refs = trace.get('refs', [])
            if refs:
                found = refs[0]
                break

    assert found is not None, "Should find ref for COVERED trace at line 5"
    assert found['file'] == 'tests/fixtures/test1/target.md'
    print("  test1/goto_definition (COVERED): OK")

    for trace in tm.get('traces', []):
        source = trace.get('source', {})
        if ls.path_matches(f"/path/to/{filepath}", source.get('file', '')) and trace.get('status') == 'MISSING':
            assert trace.get('refs', []) == [], "MISSING trace should have no refs"
    print("  test1/goto_definition (MISSING): OK")


def test_find_references():
    ls = make_server('test1')
    tm = ls._trace_map

    refs_at_7 = []
    for trace in tm.get('traces', []):
        for ref in trace.get('refs', []):
            if ls.path_matches("/path/to/tests/fixtures/test1/target.md", ref.get('file', '')) and ref.get('line') == 7:
                refs_at_7.append(trace['id'])

    assert len(refs_at_7) == 2, f"Expected 2 refs at target line 7, got {len(refs_at_7)}"
    print(f"  test1/find_references: OK ({len(refs_at_7)} refs)")


def test_code_lens():
    ls = make_server('test1')
    source_path = str(FIXTURES / 'test1' / 'source.md')
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
    print(f"  test1/code_lens: OK ({len(lenses)} lenses, {total_traces} total traces)")


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

    ls._trace_map_paths = [Path(tm_path)]
    ls._trace_map_mtimes = {tm_path: Path(tm_path).stat().st_mtime}
    ls._trace_map = json.loads(Path(tm_path).read_text(encoding='utf-8'))

    time.sleep(0.1)
    Path(src_path).touch()

    assert ls.is_stale(src_path) is True
    assert ls.is_stale("/nonexistent") is False

    os.unlink(tm_path)
    os.unlink(src_path)
    print("  test1/stale_detection: OK")


# --- test2: multi source + multi target, single trace-map ---

def test_multi_source_target():
    ls = make_server('test2')
    tm = ls._trace_map
    assert len(tm['traces']) == 32

    source_files = {t['source']['file'] for t in tm['traces']}
    assert len(source_files) == 2, f"Expected 2 source files, got {source_files}"

    kickoff_diags = ls.build_diagnostics("file:///path/to/tests/fixtures/test2/source-kickoff.md")
    followup_diags = ls.build_diagnostics("file:///path/to/tests/fixtures/test2/source-followup.md")
    assert len(kickoff_diags) > 0, "Should have diagnostics for source-kickoff"
    assert len(followup_diags) > 0, "Should have diagnostics for source-followup"

    print(f"  test2/multi_source_target: OK ({len(kickoff_diags)} kickoff, {len(followup_diags)} followup diags)")


# --- multi-trace: test1 + test2 merged (simulates discovery) ---

def test_multi_trace_merge():
    ls = make_multi_server()
    tm = ls._trace_map
    total = 12 + 32
    assert len(tm['traces']) == total, f"Expected {total} merged traces, got {len(tm['traces'])}"
    assert len(tm['reverse_traces']) == 2, "Reverse traces from test1 should be present"
    print(f"  multi/merge: OK ({total} traces, 2 reverse)")


def test_multi_trace_diagnostics():
    ls = make_multi_server()

    test1_diags = ls.build_diagnostics("file:///path/to/tests/fixtures/test1/source.md")
    test2_diags = ls.build_diagnostics("file:///path/to/tests/fixtures/test2/source-kickoff.md")

    assert len(test1_diags) > 0, "Should have diagnostics from test1"
    assert len(test2_diags) > 0, "Should have diagnostics from test2"

    print(f"  multi/diagnostics: OK (test1={len(test1_diags)}, test2={len(test2_diags)})")


def test_multi_trace_stale():
    ls = make_multi_server()

    with tempfile.NamedTemporaryFile(suffix='.md', mode='w', delete=False) as src:
        src.write("# test\n")
        src_path = src.name

    time.sleep(0.1)
    Path(src_path).touch()
    assert ls.is_stale(src_path) is True

    os.unlink(src_path)
    print("  multi/stale: OK")


if __name__ == '__main__':
    print("Running LSP integration tests...")

    print("\n--- test1: single trace-map ---")
    test_load_trace_map()
    test_no_trace_map()
    test_diagnostics_severity()
    test_diagnostics_reverse_traces()
    test_goto_definition()
    test_find_references()
    test_code_lens()
    test_stale_detection()

    print("\n--- test2: multi source+target, single trace-map ---")
    test_multi_source_target()

    print("\n--- multi-trace: test1 + test2 merged ---")
    test_multi_trace_merge()
    test_multi_trace_diagnostics()
    test_multi_trace_stale()

    print("\nAll LSP tests passed!")
