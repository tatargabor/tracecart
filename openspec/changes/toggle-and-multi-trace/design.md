## Context

The VS Code extension (`lsp/vscode-extension/extension.js`) currently:
- Loads a single `trace-map.json` from the workspace root
- Always shows all decorations (missing/partial/covered) with no way to hide them
- Shows forward and reverse traces unconditionally
- Status bar shows combined stats, click opens Problems panel

The LSP server (`lsp/server.py`) independently discovers and polls `trace-map.json` for diagnostics, code lens, go-to-definition, and find-references.

## Goals / Non-Goals

**Goals:**
- Let users toggle all decorations on/off
- Let users hide covered (green) traces to focus on problems
- Let users filter forward vs reverse traces
- Discover and merge multiple `**/trace-map.json` files
- Select a specific trace session via quick-pick
- Persist filter state across editor restarts

**Non-Goals:**
- No `.tracecart.json` config file — discovery only
- No changes to the trace-map.json schema
- No Zed extension changes (Zed has no equivalent decoration API)
- No LSP protocol changes for toggle (toggle is purely client-side decoration filtering)

## Decisions

### D1: Toggle is client-side only, not LSP

The LSP server continues to serve all diagnostics. The extension.js filters what it renders as decorations. This avoids LSP protocol complexity and keeps the server stateless.

**Alternative**: LSP workspace/configuration to tell server to filter. Rejected — adds protocol coupling for a purely visual concern.

### D2: Multi-trace discovery via glob, merged in extension

The extension uses `vscode.workspace.findFiles('**/trace-map.json', '**/node_modules/**')` to discover all trace-map files. It loads and merges them into a single in-memory structure. Each trace gets a `_session` tag (the relative path of its trace-map.json).

The LSP server also gets multi-trace support (`find_trace_map` → `find_trace_maps`) for diagnostics/code-lens, but the session selector UX is extension-only.

**Alternative**: Only discover in extension, not server. Rejected — diagnostics from LSP should also cover all trace-maps.

### D3: Session naming from path

Session name = relative directory path of the trace-map.json (e.g., `specs/auth`). Falls back to `meta.source → meta.target` if available. No user-configurable names.

### D4: State in workspace memento

VS Code's `context.workspaceState` stores: `{ enabled: boolean, showCovered: boolean, direction: 'forward'|'reverse'|'both', activeSession: string }`. Default: `{ enabled: true, showCovered: true, direction: 'both', activeSession: 'all' }`.

### D5: Status bar click behavior changes

Currently: opens Problems panel. New behavior:
- If only one trace-map: click toggles visualization on/off
- If multiple trace-maps: click opens quick-pick with session list + toggle options

## Risks / Trade-offs

- [Many trace-map.json files] → `findFiles` glob is fast, but we debounce re-discovery to avoid churn. Re-discover on file create/delete events only, not on every change.
- [Merged traces may conflict] → Two trace-maps covering the same source line show both decorations. This is correct — they represent different tracing sessions.
- [LSP server multi-trace adds complexity] → Keep it minimal: just discover multiple files and merge. The per-session filtering stays in the extension.
