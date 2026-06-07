#!/usr/bin/env python3
"""set-trace LSP server.

Reads trace-map.json and provides:
- Diagnostics: color sentences by coverage status
- Go to Definition: source trace → target section
- Find References: target section → source traces
- Code Lens: inline coverage summaries per section
- Hot Reload: polls trace-map.json mtime every 2s, auto-updates
- Stale Detection: downgrades diagnostics when source is newer than trace-map

Primary target: Zed (native LSP support)
Also works: VS Code, Neovim, Emacs, Sublime, etc.

Requires: pygls (pip install pygls)
"""

import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path

try:
    try:
        from pygls.lsp.server import LanguageServer
    except ImportError:
        from pygls.server import LanguageServer
    from lsprotocol import types
except ImportError:
    print("LSP server requires pygls: pip install pygls", file=sys.stderr)
    print("This is the only external dependency of set-trace.", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger("set-trace-lsp")

POLL_INTERVAL = 2.0

STATUS_SEVERITY = {
    'MISSING': types.DiagnosticSeverity.Error,
    'PARTIAL': types.DiagnosticSeverity.Warning,
    'COVERED': types.DiagnosticSeverity.Hint,
    'DEFERRED': types.DiagnosticSeverity.Information,
    'SUPERSEDED': types.DiagnosticSeverity.Information,
    'UNTRACED_IN_SOURCE': types.DiagnosticSeverity.Warning,
    'PARTIAL_SOURCE': types.DiagnosticSeverity.Information,
    'TRACED': types.DiagnosticSeverity.Hint,
}

SKIP_STATUSES = {'N/A', 'TRACED'}


class SetTraceServer(LanguageServer):
    def __init__(self):
        super().__init__("set-trace-lsp", "v0.3.0")
        self._trace_map: dict | None = None
        self._trace_map_paths: list[Path] = []
        self._trace_map_mtimes: dict[str, float] = {}
        self._open_uris: set[str] = set()
        self._poll_task: asyncio.Task | None = None

    def _get_roots(self) -> list[Path]:
        roots = []
        try:
            ws = self.workspace
            if ws and hasattr(ws, 'folders') and ws.folders:
                for folder in ws.folders:
                    uri = folder.uri if hasattr(folder, 'uri') else str(folder)
                    roots.append(Path(uri.replace("file://", "")))
        except RuntimeError:
            pass
        if not roots:
            roots = [Path.cwd()]
        return roots

    def find_trace_maps(self) -> list[Path]:
        found = []
        for root in self._get_roots():
            for p in root.rglob("trace-map.json"):
                if "node_modules" not in p.parts:
                    found.append(p)
        self._trace_map_paths = found
        return found

    def load_trace_maps(self) -> bool:
        paths = self.find_trace_maps()

        if not paths:
            if self._trace_map is not None:
                self._trace_map = None
                self._trace_map_mtimes = {}
                return True
            return False

        current_mtimes = {}
        for p in paths:
            try:
                current_mtimes[str(p)] = p.stat().st_mtime
            except OSError:
                pass

        if current_mtimes == self._trace_map_mtimes:
            return False

        merged = {'traces': [], 'reverse_traces': []}
        for p in paths:
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
                merged['traces'].extend(data.get('traces', []))
                merged['reverse_traces'].extend(data.get('reverse_traces', []))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to read %s: %s", p, e)

        self._trace_map = merged
        self._trace_map_mtimes = current_mtimes
        return True

    def is_stale(self, filepath: str) -> bool:
        if not self._trace_map_mtimes:
            return False
        try:
            source_mtime = os.path.getmtime(filepath)
            latest_tm = max(self._trace_map_mtimes.values()) if self._trace_map_mtimes else 0
            return source_mtime > latest_tm
        except OSError:
            return False

    def uri_to_path(self, uri: str) -> str:
        return uri.replace("file://", "")

    def path_matches(self, filepath: str, trace_file: str) -> bool:
        if not trace_file:
            return False
        return filepath.endswith(trace_file) or filepath == trace_file

    def build_diagnostics(self, uri: str) -> list[types.Diagnostic]:
        """Build diagnostics for a URI (testable without LSP connection)."""
        filepath = self.uri_to_path(uri)
        tm = self._trace_map
        if not tm:
            return []

        stale = self.is_stale(filepath)
        diagnostics = []

        for trace in tm.get('traces', []):
            source = trace.get('source', {})
            if not self.path_matches(filepath, source.get('file', '')):
                continue

            status = trace.get('status', 'UNKNOWN')
            if status in SKIP_STATUSES:
                continue

            severity = STATUS_SEVERITY.get(status, types.DiagnosticSeverity.Information)
            if stale:
                severity = types.DiagnosticSeverity.Hint

            line = max(source.get('line', 1) - 1, 0)
            col_start = source.get('col_start', 0)
            col_end = source.get('col_end', 80)

            refs_text = ", ".join(
                f"{r.get('file', '?')} {r.get('section', '')}"
                for r in trace.get('refs', [])
            )
            prefix = "[stale] " if stale else ""
            message = f"{prefix}[{status}] {trace.get('text', '')}"
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

        for rt in tm.get('reverse_traces', []):
            source = rt.get('source', {})
            if not self.path_matches(filepath, source.get('file', '')):
                continue

            status = rt.get('status', 'UNKNOWN')
            if status in SKIP_STATUSES:
                continue

            severity = STATUS_SEVERITY.get(status, types.DiagnosticSeverity.Information)
            if stale:
                severity = types.DiagnosticSeverity.Hint

            line = max(source.get('line', 1) - 1, 0)
            col_start = source.get('col_start', 0)
            col_end = source.get('col_end', 80)

            prefix = "[stale] " if stale else ""
            message = f"{prefix}[{status}] {rt.get('text', '')}"
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

        return diagnostics

    def publish_for_uri(self, uri: str):
        diagnostics = self.build_diagnostics(uri)
        try:
            self.publish_diagnostics(uri, diagnostics)
        except Exception:
            pass

    def publish_all_open(self):
        for uri in list(self._open_uris):
            self.publish_for_uri(uri)

    def get_code_lenses(self, uri: str) -> list[types.CodeLens]:
        filepath = self.uri_to_path(uri)
        tm = self._trace_map
        if not tm:
            return []

        sections: dict[int, dict] = {}

        for trace in tm.get('traces', []):
            source = trace.get('source', {})
            if not self.path_matches(filepath, source.get('file', '')):
                continue

            line = source.get('line', 0)
            status = trace.get('status', 'UNKNOWN')
            section_line = self._find_section_line(filepath, line)

            if section_line not in sections:
                sections[section_line] = {'covered': 0, 'partial': 0, 'missing': 0, 'other': 0, 'total': 0}

            s = sections[section_line]
            s['total'] += 1
            if status == 'COVERED':
                s['covered'] += 1
            elif status == 'PARTIAL':
                s['partial'] += 1
            elif status == 'MISSING':
                s['missing'] += 1
            else:
                s['other'] += 1

        lenses = []
        for section_line, counts in sorted(sections.items()):
            parts = []
            if counts['covered']:
                parts.append(f"{counts['covered']} ✓")
            if counts['partial']:
                parts.append(f"{counts['partial']} ⚠")
            if counts['missing']:
                parts.append(f"{counts['missing']} ✗")
            if counts['other']:
                parts.append(f"{counts['other']} ○")

            title = f"[set-trace] {counts['total']} traces: {'  '.join(parts)}"
            display_line = max(section_line - 1, 0)

            lenses.append(types.CodeLens(
                range=types.Range(
                    start=types.Position(line=display_line, character=0),
                    end=types.Position(line=display_line, character=0),
                ),
                command=types.Command(title=title, command=""),
            ))

        return lenses

    def _resolve_trace_path(self, file_str: str) -> Path:
        p = Path(file_str)
        if p.is_absolute():
            return p
        for tm_path in self._trace_map_paths:
            candidate = tm_path.parent / p
            if candidate.exists():
                return candidate.resolve()
        roots = self._get_roots()
        if roots:
            return (roots[0] / p).resolve()
        return p.resolve()

    def _find_section_line(self, filepath: str, trace_line: int) -> int:
        try:
            text = Path(filepath).read_text(encoding='utf-8')
        except OSError:
            return 0

        header_lines = []
        for i, line in enumerate(text.split('\n')):
            stripped = line.strip()
            if re.match(r'^#{1,4}\s+', stripped) or re.match(r'^\d+(?:\.\d+)*\s+', stripped):
                header_lines.append(i + 1)

        best = 0
        for hl in header_lines:
            if hl <= trace_line:
                best = hl
        return best


ls = SetTraceServer()


@ls.feature(types.INITIALIZED)
def on_initialized(params):
    ls.load_trace_maps()
    loop = asyncio.get_event_loop()
    ls._poll_task = loop.create_task(_poll_trace_maps())


async def _poll_trace_maps():
    while True:
        await asyncio.sleep(POLL_INTERVAL)
        try:
            changed = ls.load_trace_maps()
            if changed:
                logger.info("trace-map.json changed, refreshing diagnostics")
                ls.publish_all_open()
        except Exception as e:
            logger.debug("Poll error: %s", e)


@ls.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: types.DidOpenTextDocumentParams):
    uri = params.text_document.uri
    ls._open_uris.add(uri)
    ls.load_trace_maps()
    ls.publish_for_uri(uri)


@ls.feature(types.TEXT_DOCUMENT_DID_CLOSE)
def did_close(params: types.DidCloseTextDocumentParams):
    ls._open_uris.discard(params.text_document.uri)


@ls.feature(types.TEXT_DOCUMENT_DID_SAVE)
def did_save(params: types.DidSaveTextDocumentParams):
    ls.publish_for_uri(params.text_document.uri)


@ls.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(params: types.TextDocumentPositionParams):
    tm = ls._trace_map
    if not tm:
        return None

    filepath = ls.uri_to_path(params.text_document.uri)
    line = params.position.line + 1
    locations = []
    seen = set()

    def _make_location(file_str, target_line):
        resolved = str(ls._resolve_trace_path(file_str))
        key = (resolved, target_line)
        if key in seen:
            return None
        seen.add(key)
        return types.Location(
            uri=f"file://{resolved}",
            range=types.Range(
                start=types.Position(line=max(target_line - 1, 0), character=0),
                end=types.Position(line=max(target_line - 1, 0), character=0),
            ),
        )

    for trace in tm.get('traces', []):
        source = trace.get('source', {})
        if ls.path_matches(filepath, source.get('file', '')) and source.get('line') == line:
            for ref in trace.get('refs', []):
                if ref.get('file') and ref.get('line'):
                    loc = _make_location(ref['file'], ref['line'])
                    if loc:
                        locations.append(loc)

    for rt in tm.get('reverse_traces', []):
        source = rt.get('source', {})
        if ls.path_matches(filepath, source.get('file', '')) and source.get('line') == line:
            src_id = rt.get('source_trace_id') or rt.get('nearest_source_trace')
            if not src_id:
                continue
            for trace in tm.get('traces', []):
                if trace.get('id') == src_id:
                    src = trace.get('source', {})
                    if src.get('file'):
                        loc = _make_location(src['file'], src.get('line', 1))
                        if loc:
                            locations.append(loc)

    if not locations:
        return None
    if len(locations) == 1:
        return locations[0]
    return locations


@ls.feature(types.TEXT_DOCUMENT_REFERENCES)
def find_references(params: types.ReferenceParams):
    tm = ls._trace_map
    if not tm:
        return []

    filepath = ls.uri_to_path(params.text_document.uri)
    line = params.position.line + 1

    locations = []
    for trace in tm.get('traces', []):
        for ref in trace.get('refs', []):
            if ls.path_matches(filepath, ref.get('file', '')) and ref.get('line') == line:
                source = trace.get('source', {})
                source_path = ls._resolve_trace_path(source['file'])
                source_uri = f"file://{source_path}"
                source_line = max(source.get('line', 1) - 1, 0)
                locations.append(types.Location(
                    uri=source_uri,
                    range=types.Range(
                        start=types.Position(line=source_line, character=0),
                        end=types.Position(line=source_line, character=0),
                    ),
                ))

    return locations


@ls.feature(types.TEXT_DOCUMENT_CODE_LENS)
def code_lens(params: types.CodeLensParams):
    return ls.get_code_lenses(params.text_document.uri)


def main():
    ls.start_io()


if __name__ == '__main__':
    main()
