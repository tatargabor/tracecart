## ADDED Requirements

### Requirement: Auto-discover trace maps
The extension SHALL discover all `**/trace-map.json` files in the workspace, excluding `node_modules`. Discovery SHALL run on activation and re-run when trace-map.json files are created or deleted.

#### Scenario: Multiple trace-maps found
- **WHEN** workspace contains `specs/auth/trace-map.json` and `specs/orders/trace-map.json`
- **THEN** both are loaded and their traces are merged for decoration

#### Scenario: Single trace-map at root
- **WHEN** workspace contains only `trace-map.json` at root
- **THEN** behavior is identical to current (backward compatible)

#### Scenario: No trace-maps found
- **WHEN** no trace-map.json files exist in workspace
- **THEN** no decorations are shown and status bar is hidden

### Requirement: Merged view by default
The extension SHALL merge all discovered trace-maps into a single combined view by default. Each trace SHALL carry a `_session` tag identifying which trace-map it came from.

#### Scenario: Traces from multiple sessions on same file
- **WHEN** two trace-maps both reference the same source file
- **THEN** decorations from both sessions appear on the file

#### Scenario: Status bar shows combined stats
- **WHEN** multiple trace-maps are loaded in merged view
- **THEN** status bar shows combined coverage statistics across all sessions

### Requirement: Session selector
The extension SHALL provide a `set-trace: Select Session` command that opens a quick-pick with all discovered sessions plus an "All sessions" option. Selecting a session filters decorations to only that session's traces.

#### Scenario: Select specific session
- **WHEN** user runs `set-trace: Select Session` and picks "specs/auth"
- **THEN** only traces from `specs/auth/trace-map.json` are shown
- **THEN** status bar shows stats for that session only

#### Scenario: Select all sessions
- **WHEN** user runs `set-trace: Select Session` and picks "All sessions"
- **THEN** merged view is restored with all traces visible

### Requirement: Session naming
Session names SHALL be derived from the relative directory path of each trace-map.json within the workspace. The root trace-map.json SHALL be named "(root)".

#### Scenario: Nested trace-map naming
- **WHEN** trace-map.json is at `specs/auth/trace-map.json`
- **THEN** session name is "specs/auth"

#### Scenario: Root trace-map naming
- **WHEN** trace-map.json is at workspace root
- **THEN** session name is "(root)"

### Requirement: LSP server multi-trace support
The LSP server SHALL discover and serve diagnostics from all `**/trace-map.json` files in the workspace, not just the root one.

#### Scenario: Diagnostics from multiple trace-maps
- **WHEN** workspace has multiple trace-map.json files
- **THEN** LSP diagnostics include traces from all of them

#### Scenario: Hot reload for all trace-maps
- **WHEN** any trace-map.json file changes
- **THEN** LSP server reloads that file and republishes diagnostics
