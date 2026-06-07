## ADDED Requirements

### Requirement: Auto-reload on trace-map.json change
The LSP server SHALL detect when trace-map.json is modified on disk and automatically re-read it and update diagnostics for all open files.

#### Scenario: Pipeline re-run updates editor
- **WHEN** the user re-runs the tracecart pipeline and trace-map.json is updated
- **THEN** within 3 seconds, the editor diagnostics reflect the new coverage data

### Requirement: Polling-based detection
The LSP server SHALL use mtime polling (every 2 seconds) to detect trace-map.json changes. No external file-watcher dependency required.

#### Scenario: Low resource usage
- **WHEN** the LSP server is running idle (no trace-map.json changes)
- **THEN** it uses negligible CPU (one stat() call every 2 seconds)

### Requirement: Stale diagnostics indicator
The LSP server SHALL detect when source files have been modified after trace-map.json was generated, and indicate that diagnostics may be stale.

#### Scenario: Source file edited after pipeline
- **WHEN** a source file's mtime is newer than trace-map.json's mtime
- **THEN** diagnostics for that file are downgraded to Hint severity with a "[stale]" prefix

### Requirement: Clean removal of diagnostics
When trace-map.json is deleted or a file is removed from the trace-map, the LSP server SHALL clear all diagnostics for that file.

#### Scenario: trace-map.json deleted
- **WHEN** trace-map.json is removed from disk
- **THEN** all diagnostics are cleared from all open files within 3 seconds
