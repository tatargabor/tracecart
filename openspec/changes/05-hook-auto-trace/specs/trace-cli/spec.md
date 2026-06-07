## ADDED Requirements

### Requirement: CLI check command
The system SHALL provide a CLI entrypoint for running trace verification manually, independent of the hook system.

#### Scenario: Run all mappings
- **WHEN** the user runs `python3 -m set_trace check`
- **THEN** the system reads `.tracecart/config.json`, runs the pipeline for all mappings, and prints results to stdout

#### Scenario: Run specific mapping
- **WHEN** the user runs `python3 -m set_trace check --mapping order-intake`
- **THEN** the system runs the pipeline only for the "order-intake" mapping

#### Scenario: Ad-hoc source and target
- **WHEN** the user runs `python3 -m set_trace check --source meetings/2024-03-15.md --target specs/order-intake.md`
- **THEN** the system runs the pipeline with the specified files, without requiring a config file

### Requirement: CLI output format
The CLI SHALL produce the same stdout summary format as the hook, plus write trace-map.json to the output directory.

#### Scenario: CLI output matches hook output
- **WHEN** the CLI runs on the same files as the hook would
- **THEN** the stdout format and trace-map.json content are identical

### Requirement: Exit codes
The CLI SHALL use meaningful exit codes for CI integration.

#### Scenario: All traces covered
- **WHEN** forward coverage is 100% and no UNTRACED_IN_SOURCE claims exist
- **THEN** exit code is 0

#### Scenario: Findings exist
- **WHEN** there are MISSING, PARTIAL, or UNTRACED_IN_SOURCE findings
- **THEN** exit code is 1

#### Scenario: Error
- **WHEN** the pipeline fails (invalid config, LLM error, file not found)
- **THEN** exit code is 2 with error message to stderr
