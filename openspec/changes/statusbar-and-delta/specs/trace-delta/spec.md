## ADDED Requirements

### Requirement: Delta comparison between two trace-maps
The system SHALL provide a `delta` subcommand that compares two trace-map.json files and reports what changed.

#### Scenario: Coverage improved
- **WHEN** running `python3 src/run_trace.py delta old.json new.json`
- **THEN** the output lists traces that improved (e.g. MISSING→COVERED) under "IMPROVED" section

#### Scenario: Coverage regressed
- **WHEN** a trace that was COVERED in old.json is PARTIAL in new.json
- **THEN** the output lists it under "REGRESSED" section

#### Scenario: New traces appeared
- **WHEN** new.json contains trace IDs not present in old.json
- **THEN** the output lists them under "NEW" section

#### Scenario: Traces disappeared
- **WHEN** old.json contains trace IDs not present in new.json
- **THEN** the output lists them under "REMOVED" section

### Requirement: Delta summary statistics
The delta output SHALL include summary statistics showing coverage change.

#### Scenario: Summary line
- **WHEN** forward coverage changed from 72.5% to 79.7%
- **THEN** the output shows "Forward: 72.5% → 79.7% (+7.2%)"

### Requirement: JSON output format
The delta command SHALL support a `--json` flag for machine-readable output.

#### Scenario: JSON output for LLM agent
- **WHEN** running with `--json` flag
- **THEN** the output is valid JSON with keys: summary, improved, regressed, new, removed

### Requirement: Text fallback matching
When a trace ID is not found in the other trace-map, the system SHALL attempt to match by trace text similarity as a fallback.

#### Scenario: Source line shifted causing new trace ID
- **WHEN** a trace text exists in both maps but with different IDs due to line shift
- **THEN** the delta reports it as a status change (improved/regressed) rather than removed+new
