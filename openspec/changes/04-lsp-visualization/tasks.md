## 1. LSP Server Core

- [x] 1.1 Implement production diagnostics: read trace-map.json, publish per-file diagnostics with correct severity mapping
- [x] 1.2 Implement go-to-definition: source trace line → target file:line navigation
- [x] 1.3 Implement find-references: target section → list of source trace locations
- [x] 1.4 Implement code lens: aggregate traces per section, show summary above headers
- [x] 1.5 Add graceful degradation: no crash when trace-map.json missing, silent startup

## 2. Hot Reload

- [x] 2.1 Implement mtime polling (2-second interval) for trace-map.json
- [x] 2.2 On change detected: re-read, re-publish diagnostics for all open files
- [x] 2.3 On delete detected: clear all diagnostics
- [x] 2.4 Implement stale detection: compare source file mtime vs trace-map mtime, downgrade to Hint if stale
- [x] 2.5 Test: modify trace-map.json → verify editor updates within 3 seconds

## 3. Zed Extension

- [x] 3.1 Create extension manifest (extension.toml) for Zed
- [x] 3.2 Configure activation condition: only when trace-map.json exists in workspace
- [x] 3.3 Configure language association: markdown files
- [x] 3.4 Write extension README (install, prerequisites, usage)
- [x] 3.5 Test: install extension in Zed, open project with trace-map.json, verify diagnostics appear

## 4. Integration Testing

- [x] 4.1 Create a test trace-map.json with known content (5 files, 20 traces, mixed statuses)
- [x] 4.2 Verify diagnostics: open source file → correct colors on correct lines
- [x] 4.3 Verify navigation: go-to-definition jumps to correct target location
- [x] 4.4 Verify references: find-references from target lists correct source locations
- [x] 4.5 Verify code lens: section summaries show correct counts
- [x] 4.6 Verify hot-reload: update trace-map.json → diagnostics refresh
