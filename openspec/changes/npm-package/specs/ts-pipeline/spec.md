## ADDED Requirements

### Requirement: clause-split produces identical output
The TypeScript `clauseSplit` module SHALL produce byte-identical JSON output to the Python `clause_split.py` for the same input text.

#### Scenario: Single-line clauses
- **WHEN** input text has one clause per line
- **THEN** each line produces one clause object with `line_number`, `clause_index: 0`, `text`, `is_header`

#### Scenario: Compound lines
- **WHEN** a line contains multiple clauses (split by `;`, `:`, etc.)
- **THEN** each sub-clause gets a separate object with incrementing `clause_index`

#### Scenario: Fixture test1
- **WHEN** `tests/fixtures/test1/` source files are processed
- **THEN** output matches the reference clauses JSON

### Requirement: extract module produces identical output
The TypeScript `extract` module SHALL produce identical prompt formatting and validation results to the Python `extract.py`.

#### Scenario: format prompt
- **WHEN** `formatPrompt(clauses, options)` is called with clauses JSON
- **THEN** the returned prompt string matches the Python `format_prompt` output for the same input

#### Scenario: validate traces
- **WHEN** `validateTraces(rawLlmOutput, clauses)` is called with LLM output text
- **THEN** the returned traces JSON matches the Python `validate_traces` output — same IDs, same clause references, same types

#### Scenario: merge traces across iterations
- **WHEN** `mergeTraces(existing, newTraces)` is called
- **THEN** traces are merged by ID with new overriding old, identical to Python `merge_traces`

### Requirement: remainder module produces identical output
The TypeScript `remainder` module SHALL compute identical remainder statistics to Python `remainder.py`.

#### Scenario: Full coverage
- **WHEN** all clauses are consumed by traces
- **THEN** `isComplete` returns true and `uncoveredRatio` is 0

#### Scenario: Partial coverage
- **WHEN** some clauses are not referenced by any trace
- **THEN** `computeRemainder` returns the uncovered clause IDs and ratio, matching Python output

### Requirement: coverage module produces identical output
The TypeScript `coverage` module SHALL produce identical prompt formatting and match validation to Python `coverage.py`.

#### Scenario: format match prompt
- **WHEN** `formatPrompt(traces, targetText)` is called
- **THEN** the returned prompt matches the Python `format_prompt` output

#### Scenario: validate matches
- **WHEN** `validateMatches(rawLlmOutput, traces)` is called
- **THEN** coverage statuses (COVERED, PARTIAL, MISSING, DEFERRED, N/A) match Python output

#### Scenario: reverse matching
- **WHEN** reverse trace functions (`formatReversePrompt`, `validateReverseMatches`, `applyReverseMatches`) are called
- **THEN** output matches the Python reverse matching functions

### Requirement: trace-map module produces identical output
The TypeScript `traceMap` module SHALL produce identical `trace-map.json` structure to Python `trace_map.py`.

#### Scenario: Build trace map
- **WHEN** `buildTraceMap(traces, matches, options)` is called
- **THEN** the output JSON has the same structure: `meta`, `traces[]`, `summary`, `diagnostics`

#### Scenario: Coverage summary
- **WHEN** `computeSummary(traces)` is called
- **THEN** counts per coverage status match Python output

### Requirement: delta module produces identical output
The TypeScript `delta` module SHALL produce identical comparison results to Python `delta.py`.

#### Scenario: Compare two trace maps
- **WHEN** `compare(oldMap, newMap)` is called
- **THEN** added/removed/changed traces are identical to Python output

### Requirement: parse-document module produces identical output
The TypeScript `parseDocument` module SHALL produce identical chapter detection to Python `parse_document.py`.

#### Scenario: Chapter detection
- **WHEN** a markdown document with headers is parsed
- **THEN** chapter boundaries match the Python output

### Requirement: discover-inputs module produces identical output
The TypeScript `discoverInputs` module SHALL produce identical file discovery to Python `discover_inputs.py`.

#### Scenario: Source/target classification
- **WHEN** files in a directory are classified
- **THEN** document types and dates match the Python output
