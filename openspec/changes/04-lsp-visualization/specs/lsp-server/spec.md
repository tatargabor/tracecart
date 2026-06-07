## ADDED Requirements

### Requirement: Diagnostics by coverage status
The LSP server SHALL publish diagnostics for each trace in the currently opened file, with severity mapped to coverage status: MISSING=Error, PARTIAL=Warning, COVERED=Hint, DEFERRED=Information.

#### Scenario: MISSING trace shows as error
- **WHEN** a source file is opened containing a trace with status MISSING
- **THEN** the editor shows a red error diagnostic on that line with the trace text

#### Scenario: COVERED trace shows as hint
- **WHEN** a source file is opened containing a trace with status COVERED
- **THEN** the editor shows a subtle hint diagnostic (not distracting) with the trace text and target reference

#### Scenario: N/A trace shows nothing
- **WHEN** a source file is opened containing a trace with status N/A
- **THEN** no diagnostic is published for that line

### Requirement: Go to Definition (source → target)
The LSP server SHALL respond to "Go to Definition" on a source trace line by navigating to the target file and line that covers it.

#### Scenario: Navigate to target section
- **WHEN** user triggers "Go to Definition" on a line with a COVERED trace
- **THEN** the editor opens the target file at the referenced line/section

#### Scenario: No definition for MISSING trace
- **WHEN** user triggers "Go to Definition" on a line with a MISSING trace
- **THEN** no navigation occurs (no target exists)

### Requirement: Find References (target → source)
The LSP server SHALL respond to "Find References" on a target section by listing all source traces that map to it.

#### Scenario: List source traces
- **WHEN** user triggers "Find References" on a target section line
- **THEN** the editor shows a list of all source file locations whose traces reference this section

### Requirement: Code Lens (section summaries)
The LSP server SHALL display a code lens above section headers showing trace coverage counts for that section.

#### Scenario: Section summary display
- **WHEN** a source file has a section header with 8 traces below it (5 COVERED, 2 PARTIAL, 1 MISSING)
- **THEN** a code lens appears above the header: "[tracecart] 8 traces: 5 ✓  2 ⚠  1 ✗"

### Requirement: Graceful degradation
The LSP server SHALL start without errors even if trace-map.json does not exist. It SHALL produce no diagnostics until a valid trace-map.json appears.

#### Scenario: No trace-map.json
- **WHEN** the editor opens a file but no trace-map.json exists in the workspace
- **THEN** the LSP server runs silently with no diagnostics, no errors
