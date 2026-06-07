#!/usr/bin/env python3
"""set-trace LSP server.

Reads trace-map.json and provides:
- Diagnostics: color sentences by coverage status
- Go to Definition: source trace → target section
- Find References: target section → source traces
- Code Lens: inline coverage summaries

Primary target: Zed (native LSP support)
Also works: VS Code, Neovim, Emacs, Sublime, etc.

Requires: pygls (pip install pygls)
"""

# TODO: Implement when core pipeline produces trace-map.json
# Skeleton below shows the LSP structure.

import json
import sys
from pathlib import Path

try:
    from pygls.server import LanguageServer
    from lsprotocol import types
except ImportError:
    print("LSP server requires pygls: pip install pygls", file=sys.stderr)
    print("This is the only external dependency of set-trace.", file=sys.stderr)
    sys.exit(1)


TRACE_MAP_PATH = "trace-map.json"

server = LanguageServer("set-trace-lsp", "v0.1.0")


def load_trace_map(path: str = TRACE_MAP_PATH) -> dict | None:
    """Load trace-map.json from project root."""
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding='utf-8'))


def status_to_severity(status: str) -> types.DiagnosticSeverity:
    """Map trace status to LSP diagnostic severity."""
    return {
        'MISSING': types.DiagnosticSeverity.Error,
        'PARTIAL': types.DiagnosticSeverity.Warning,
        'COVERED': types.DiagnosticSeverity.Hint,
        'DEFERRED': types.DiagnosticSeverity.Information,
        'SUPERSEDED': types.DiagnosticSeverity.Information,
        'UNTRACED_IN_SOURCE': types.DiagnosticSeverity.Warning,
        'PARTIAL_SOURCE': types.DiagnosticSeverity.Information,
        'TRACED': types.DiagnosticSeverity.Hint,
    }.get(status, types.DiagnosticSeverity.Information)


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: types.DidOpenTextDocumentParams):
    """Publish diagnostics when a file is opened."""
    trace_map = load_trace_map()
    if not trace_map:
        return

    uri = params.text_document.uri
    filepath = uri.replace("file://", "")

    diagnostics = []
    for trace in trace_map.get('traces', []):
        source = trace.get('source', {})
        if not filepath.endswith(source.get('file', '')):
            continue

        line = source.get('line', 1) - 1
        col_start = source.get('col_start', 0)
        col_end = source.get('col_end', 80)

        status = trace.get('status', 'UNKNOWN')
        severity = status_to_severity(status)

        refs_text = ", ".join(
            f"{r.get('file', '?')} {r.get('section', '')}"
            for r in trace.get('refs', [])
        )
        message = f"[{status}] {trace.get('text', '')}"
        if refs_text:
            message += f"\n→ {refs_text}"

        diagnostics.append(types.Diagnostic(
            range=types.Range(
                start=types.Position(line=line, character=col_start),
                end=types.Position(line=line, character=col_end),
            ),
            severity=severity,
            source="set-trace",
            message=message,
        ))

    for rt in trace_map.get('reverse_traces', []):
        source = rt.get('source', {})
        if not filepath.endswith(source.get('file', '')):
            continue

        status = rt.get('status', 'UNKNOWN')
        if status not in ('UNTRACED_IN_SOURCE', 'PARTIAL_SOURCE'):
            continue

        line = source.get('line', 1) - 1
        col_start = source.get('col_start', 0)
        col_end = source.get('col_end', 80)
        severity = status_to_severity(status)

        message = f"[{status}] {rt.get('text', '')}"
        nearest = rt.get('nearest_source_trace')
        if nearest:
            note = rt.get('similarity_note', '')
            message += f"\n~ nearest: {nearest}"
            if note:
                message += f" ({note})"

        diagnostics.append(types.Diagnostic(
            range=types.Range(
                start=types.Position(line=line, character=col_start),
                end=types.Position(line=line, character=col_end),
            ),
            severity=severity,
            source="set-trace-reverse",
            message=message,
        ))

    server.publish_diagnostics(uri, diagnostics)


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(params: types.TextDocumentPositionParams):
    """Go to Definition: jump from source trace to target section."""
    trace_map = load_trace_map()
    if not trace_map:
        return None

    uri = params.text_document.uri
    filepath = uri.replace("file://", "")
    line = params.position.line + 1

    for trace in trace_map.get('traces', []):
        source = trace.get('source', {})
        if filepath.endswith(source.get('file', '')) and source.get('line') == line:
            refs = trace.get('refs', [])
            if refs:
                ref = refs[0]
                target_uri = f"file://{Path(ref['file']).resolve()}"
                target_line = ref.get('line', 1) - 1
                return types.Location(
                    uri=target_uri,
                    range=types.Range(
                        start=types.Position(line=target_line, character=0),
                        end=types.Position(line=target_line, character=0),
                    ),
                )
    return None


@server.feature(types.TEXT_DOCUMENT_REFERENCES)
def find_references(params: types.ReferenceParams):
    """Find References: from target section, find all source traces."""
    trace_map = load_trace_map()
    if not trace_map:
        return []

    uri = params.text_document.uri
    filepath = uri.replace("file://", "")
    line = params.position.line + 1

    locations = []
    for trace in trace_map.get('traces', []):
        for ref in trace.get('refs', []):
            if filepath.endswith(ref.get('file', '')) and ref.get('line') == line:
                source = trace.get('source', {})
                source_uri = f"file://{Path(source['file']).resolve()}"
                source_line = source.get('line', 1) - 1
                locations.append(types.Location(
                    uri=source_uri,
                    range=types.Range(
                        start=types.Position(line=source_line, character=0),
                        end=types.Position(line=source_line, character=0),
                    ),
                ))

    return locations


def main():
    """Start the LSP server."""
    server.start_io()


if __name__ == '__main__':
    main()
