## ADDED Requirements

### Requirement: Clause splitting before extraction
The system SHALL split source document text into atomic clauses using the deterministic clause splitter before passing to LLM extraction. Each clause SHALL have a unique clause_id (format: L{line}-C{index}).

#### Scenario: Compound sentence splitting
- **WHEN** a source document contains "A visszaigazolásnak figyelembe kell vennie a faanyag-készletet, a CNC kapacitást, a felületkezelési időt és a szállítási ütemezést"
- **THEN** the clause splitter produces 4 separate clauses, each with a unique clause_id

#### Scenario: Simple sentence passthrough
- **WHEN** a source document contains a simple sentence with no compound structure
- **THEN** the clause splitter produces 1 clause with clause_id L{line}

### Requirement: LLM-based trace extraction from clauses
The system SHALL extract atomic traces from clauses using an LLM subagent. Each extracted trace SHALL reference the clause_id(s) it was derived from.

#### Scenario: Explicit trace extraction
- **WHEN** the LLM receives a clause "Elsődleges rendelési csatorna: B2B portál"
- **THEN** it produces a trace with type REQUIREMENT, the original text, and the source clause_id

#### Scenario: Implicit trace extraction
- **WHEN** the LLM receives a clause containing "B2B portál"
- **THEN** it MAY produce an additional implicit trace (e.g., "not end-consumer") with implicit=true and a signal field explaining the inference

### Requirement: Recursive remainder tracking
The system SHALL track which clauses have been consumed by extracted traces and compute the remainder (untraced clauses). Extraction SHALL repeat on the remainder until either the remainder is empty or the remainder did not shrink since the last iteration.

#### Scenario: Full consumption
- **WHEN** all source clauses are referenced by at least one extracted trace
- **THEN** the remainder is empty and extraction terminates with complete=true

#### Scenario: Remainder shrinks
- **WHEN** the first extraction pass leaves 5 untraced clauses, and the second pass traces 3 of them
- **THEN** a third pass runs on the remaining 2 untraced clauses

#### Scenario: Remainder does not shrink
- **WHEN** a pass produces no new traces from the remainder
- **THEN** extraction terminates and the untraced clauses are logged

#### Scenario: Maximum iterations
- **WHEN** 3 extraction passes have been executed
- **THEN** extraction terminates regardless of remainder size

### Requirement: Trace output format
Each extracted trace SHALL include: id, text, type (REQUIREMENT|DECISION|WISH|OPEN_QUESTION|EXCLUSION), source location (file, line, col_start, col_end), clause_id reference, topics list, implicit flag, and optionally a triple (subject, attribute, object).

#### Scenario: Complete trace record
- **WHEN** extraction produces a trace
- **THEN** the trace JSON contains all required fields with non-null values

#### Scenario: Traces output as JSON
- **WHEN** extraction completes
- **THEN** all traces are written to a JSON file with a traces array and extraction_stats object
