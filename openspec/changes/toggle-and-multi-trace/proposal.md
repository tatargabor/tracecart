## Why

The VS Code extension shows all trace decorations unconditionally — no way to hide them, filter by status, or focus on a specific trace session. In projects with multiple source-target pairs, only one `trace-map.json` at the workspace root is supported, so you can't visualize multiple tracing sessions side by side.

## What Changes

- **Toggle commands**: three new VS Code commands to control visualization visibility:
  - `set-trace: Toggle Visualization` — master on/off switch (status bar click also toggles)
  - `set-trace: Toggle Covered` — hide/show covered (green) decorations to reduce visual noise
  - `set-trace: Toggle Direction` — cycle through forward / reverse / both
- **Multi-trace discovery**: auto-discover all `**/trace-map.json` files in the workspace, not just the root
- **Session selector**: merged view by default, with quick-pick to filter to a specific trace session
- **Session naming**: auto-generate session names from trace-map `meta.source` + `meta.target`
- **Filter state persistence**: toggle/filter state saved in workspace memento across editor restarts

## Capabilities

### New Capabilities
- `visualization-toggle`: Commands and state management for toggling decoration visibility and filtering by status/direction
- `multi-trace-session`: Discovery, merging, and selection of multiple trace-map.json files across the workspace

### Modified Capabilities

(none — no existing specs)

## Impact

- `lsp/vscode-extension/extension.js` — main changes: toggle state, multi-file discovery, session selector, decoration filtering
- `lsp/vscode-extension/package.json` — register new commands and keybindings
- `lsp/server.py` — multi trace-map discovery support (find all `**/trace-map.json`, serve merged data)
- No new dependencies, no breaking changes
