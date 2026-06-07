## Context

The `lsp/server.py` skeleton already exists with basic structure: diagnostics on file open, go-to-definition, find-references. This change makes it production-ready with hot-reload, proper error handling, and Zed integration.

The LSP approach means we support every editor without maintaining separate plugins — one server, universal protocol.

## Goals / Non-Goals

**Goals:**
- Working Zed integration (open markdown file → see coverage colors)
- Bidirectional navigation (source↔target in one click)
- Hot-reload (re-run pipeline → editor updates automatically)
- Code lens showing per-section coverage summaries
- Graceful degradation (no trace-map.json → no diagnostics, no crash)

**Non-Goals:**
- VS Code extension (follow-up, after Zed works)
- Interactive editing of trace-map.json from the editor
- Real-time pipeline execution from the editor (user runs pipeline separately)
- Custom syntax highlighting (using existing markdown highlighting)
- Hover documentation (v2 — show full trace details on hover)

## Decisions

### 1. Zed extension: language server manifest

Zed uses a `extension.toml` manifest to register language servers. Our extension:
- Activates on markdown files (`.md`)
- Only activates if `trace-map.json` exists in the workspace root
- Points to `lsp/server.py` as the server binary

```toml
[language_servers.set-trace]
name = "set-trace"
language = "Markdown"
```

### 2. Hot-reload via file watcher

The LSP server watches `trace-map.json` for changes using `watchdog` or simple polling (check mtime every 2 seconds). On change:
1. Re-read trace-map.json
2. Re-publish diagnostics for all open files
3. Clear diagnostics for files no longer in the trace-map

**Why polling over watchdog:** Fewer dependencies. The file only changes when the pipeline runs (not continuously), so 2-second polling is fine.

### 3. Diagnostic severity mapping

| Coverage status | LSP severity | Visual in editor |
|----------------|-------------|-----------------|
| MISSING | Error (red) | Red underline/highlight |
| PARTIAL | Warning (yellow) | Yellow underline/highlight |
| COVERED | Hint (green/subtle) | Subtle green or dimmed |
| DEFERRED | Information (blue) | Blue/info marker |
| N/A | (no diagnostic) | No visual indicator |

COVERED traces get Hint severity (visible but not distracting). N/A traces produce no diagnostic at all.

### 4. Code lens format

Above each section header in source documents:
```
[set-trace] 8 traces: 5 ✓  2 ⚠  1 ✗
```

This requires aggregating traces per source file section. The LSP server groups traces by their source line ranges and the nearest preceding header.

### 5. pygls as the only dependency

The LSP server uses pygls (Python LSP framework). This is the project's only external dependency. Installation: `pip install pygls`.

No venv/docker/nix required — just pip install one package.

## Risks / Trade-offs

**[Risk] Zed extension API changes** — Zed's extension system is still evolving.
→ Mitigation: Keep the extension minimal (just a manifest pointing to the server). All logic is in the server, which speaks standard LSP.

**[Risk] Large trace-map.json slows down diagnostics** — At 2000 traces, publishing diagnostics for all open files on every change could be slow.
→ Mitigation: Only publish diagnostics for currently open files. Lazy-load trace data per file.

**[Risk] Editor shows stale diagnostics** — If user edits source files after pipeline ran, line numbers shift.
→ Mitigation: Show a "stale" indicator (e.g., all diagnostics downgraded to Hint) if trace-map.json is older than the source file's mtime. The user re-runs the pipeline to refresh.

**[Risk] Multiple workspace folders** — trace-map.json might not be in workspace root.
→ Mitigation: Search upward from opened file for nearest trace-map.json (like .git search).
