## ADDED Requirements

### Requirement: trace-map.json format
The system SHALL produce a trace-map.json file containing: version number, generation timestamp, source file list, target file list, traces array with statuses and references, and a summary object.

#### Scenario: Complete trace-map structure
- **WHEN** extraction and matching complete
- **THEN** trace-map.json contains version=1, generated timestamp, source_files, target_files, traces array, and summary

### Requirement: Coverage summary
The trace-map.json SHALL include a summary object with counts for each status (covered, partial, missing, deferred, na) and a coverage_score_pct calculated as (covered + partial × 0.5) / (covered + partial + missing) × 100. SUPERSEDED is reserved for v2 (always 0 in v1). PARTIAL counts as half-covered in the score.

#### Scenario: Summary calculation
- **WHEN** there are 10 COVERED, 4 PARTIAL, and 6 MISSING traces
- **THEN** summary shows coverage_score_pct = 60.0 ((10 + 4×0.5) / (10 + 4 + 6) × 100)

### Requirement: Untraced clauses tracking
The trace-map.json SHALL include an untraced_clauses array listing any source clauses that were not consumed by any extracted trace after the remainder loop completed.

#### Scenario: All clauses consumed
- **WHEN** the remainder loop terminates with empty remainder
- **THEN** untraced_clauses is an empty array

#### Scenario: Some clauses untraced
- **WHEN** the remainder loop terminates with 3 untraced clauses
- **THEN** untraced_clauses contains 3 entries with clause_id and text

### Requirement: Source annotations
The trace-map.json SHALL provide enough information to annotate source documents: for each trace, the source file path, line number, column range, status, and target references.

#### Scenario: Source annotation data present
- **WHEN** a trace is extracted from line 47 of meetings/2024-01-15.md
- **THEN** the trace's source object contains file, line, col_start, col_end

### Requirement: JSON output only
The trace-map.json SHALL be valid JSON, UTF-8 encoded, with no binary content. It SHALL be diffable in git.

#### Scenario: Valid JSON output
- **WHEN** the pipeline completes
- **THEN** the output file is parseable by `json.loads()` without errors
