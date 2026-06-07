## ADDED Requirements

### Requirement: Status bar shows coverage summary
The VS Code extension SHALL display a status bar item showing the forward coverage percentage and trace status counts from the loaded trace-map.json.

#### Scenario: trace-map.json loaded with mixed coverage
- **WHEN** a trace-map.json is loaded with 24 COVERED, 3 PARTIAL, 5 MISSING traces
- **THEN** the status bar shows "tracecart: 79.7% | 24✓ 3⚠ 5✗"

#### Scenario: No trace-map.json found
- **WHEN** the workspace has no trace-map.json
- **THEN** the status bar item is hidden

#### Scenario: trace-map.json includes reverse traces
- **WHEN** the trace-map.json contains both forward and reverse trace data
- **THEN** the status bar shows forward and reverse: "tracecart: 79.7% ↔ 85.0%"

### Requirement: Status bar click action
The status bar item SHALL open the VS Code Problems panel when clicked.

#### Scenario: User clicks status bar
- **WHEN** the user clicks the tracecart status bar item
- **THEN** VS Code opens the Problems panel

### Requirement: Status bar updates on trace-map change
The status bar item SHALL update when the trace-map.json file changes on disk.

#### Scenario: Pipeline re-run updates trace-map.json
- **WHEN** the trace-map.json file is modified
- **THEN** the status bar item refreshes to show updated coverage numbers within 3 seconds
