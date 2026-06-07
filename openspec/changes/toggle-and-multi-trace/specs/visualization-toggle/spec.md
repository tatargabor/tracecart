## ADDED Requirements

### Requirement: Master visualization toggle
The extension SHALL provide a `tracecart: Toggle Visualization` command that switches all trace decorations on or off. When off, no decorations, code lenses, or hover messages SHALL be rendered. The status bar SHALL show "(off)" when disabled.

#### Scenario: Toggle off hides everything
- **WHEN** user runs `tracecart: Toggle Visualization` while decorations are visible
- **THEN** all decorations (missing, partial, covered) are removed from all open editors
- **THEN** status bar text shows "tracecart (off)"

#### Scenario: Toggle on restores decorations
- **WHEN** user runs `tracecart: Toggle Visualization` while decorations are hidden
- **THEN** decorations reappear according to current filter settings (covered toggle, direction)

#### Scenario: Status bar click toggles
- **WHEN** user clicks the status bar item
- **THEN** visualization toggles on/off (same as running the command)

### Requirement: Covered traces toggle
The extension SHALL provide a `tracecart: Toggle Covered` command that hides or shows covered/traced (green) decorations. This allows focusing on missing and partial traces.

#### Scenario: Hide covered traces
- **WHEN** user runs `tracecart: Toggle Covered` while covered traces are visible
- **THEN** covered and traced decorations are removed
- **THEN** missing and partial decorations remain visible

#### Scenario: Show covered traces
- **WHEN** user runs `tracecart: Toggle Covered` while covered traces are hidden
- **THEN** covered and traced decorations reappear

### Requirement: Direction filter toggle
The extension SHALL provide a `tracecart: Toggle Direction` command that cycles through: both → forward only → reverse only → both.

#### Scenario: Cycle to forward only
- **WHEN** user runs `tracecart: Toggle Direction` while direction is "both"
- **THEN** only forward traces are shown, reverse traces are hidden

#### Scenario: Cycle to reverse only
- **WHEN** user runs `tracecart: Toggle Direction` while direction is "forward"
- **THEN** only reverse traces are shown, forward traces are hidden

#### Scenario: Cycle back to both
- **WHEN** user runs `tracecart: Toggle Direction` while direction is "reverse"
- **THEN** both forward and reverse traces are shown

### Requirement: Filter state persistence
Toggle and filter state SHALL be persisted in VS Code workspace memento so settings survive editor restarts.

#### Scenario: State survives restart
- **WHEN** user disables covered traces and restarts VS Code
- **THEN** covered traces remain hidden after restart

#### Scenario: Default state
- **WHEN** extension activates for the first time in a workspace
- **THEN** state defaults to: enabled=true, showCovered=true, direction=both
