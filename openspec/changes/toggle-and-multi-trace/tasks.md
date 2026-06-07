## 1. Toggle & Filter State

- [x] 1.1 Add toggle state object to extension.js: `{ enabled, showCovered, direction, activeSession }` with workspace memento load/save
- [x] 1.2 Add `applyDecorations` filter logic: skip decorations based on toggle state (enabled, showCovered, direction)
- [x] 1.3 Register `tracecart.toggleVisualization` command — flips `enabled`, calls `refreshAll`
- [x] 1.4 Register `tracecart.toggleCovered` command — flips `showCovered`, calls `refreshAll`
- [x] 1.5 Register `tracecart.toggleDirection` command — cycles `both→forward→reverse→both`, calls `refreshAll`
- [x] 1.6 Update status bar: show "(off)" when disabled, reflect current filter state
- [x] 1.7 Change status bar click to toggle on/off (single trace-map) or open quick-pick (multiple)

## 2. Multi-trace Discovery (Extension)

- [x] 2.1 Replace `findTraceMap()` with `discoverTraceMaps()` using `vscode.workspace.findFiles('**/trace-map.json', '**/node_modules/**')`
- [x] 2.2 Replace `loadTraceMap()` with `loadAllTraceMaps()` — load each discovered file, tag traces with `_session` (relative dir path)
- [x] 2.3 Merge all trace-maps into single in-memory structure for `applyDecorations`
- [x] 2.4 Update file watcher to watch `**/trace-map.json` create/delete/change events and re-discover

## 3. Session Selector

- [x] 3.1 Register `tracecart.selectSession` command — opens quick-pick with "All sessions" + discovered session names
- [x] 3.2 Filter `applyDecorations` and `updateStatusBar` by `activeSession` state
- [x] 3.3 Session naming: relative dir path, "(root)" for workspace root

## 4. Package.json & Commands

- [x] 4.1 Add all new commands to `package.json` contributes.commands
- [x] 4.2 Add keybinding for toggle visualization

## 5. LSP Server Multi-trace

- [x] 5.1 Replace `find_trace_map()` with `find_trace_maps()` — glob `**/trace-map.json` under workspace roots
- [x] 5.2 Replace `load_trace_map()` with `load_trace_maps()` — load all, merge, track mtimes per file
- [x] 5.3 Update poll loop to check all discovered trace-map files

## 6. Testing

- [ ] 6.1 Manual test: toggle on/off with single trace-map
- [ ] 6.2 Manual test: toggle covered hides green decorations
- [ ] 6.3 Manual test: direction cycling filters forward/reverse
- [ ] 6.4 Manual test: multi trace-map discovery and merged view
- [ ] 6.5 Manual test: session selector filters to single session
- [ ] 6.6 Manual test: state persists across editor restart
