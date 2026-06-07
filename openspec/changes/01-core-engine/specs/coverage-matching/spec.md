## ADDED Requirements

### Requirement: Trace-to-target matching
The system SHALL compare each extracted trace against target document sections and assign a coverage status using an LLM subagent.

#### Scenario: Fully covered trace
- **WHEN** a trace states "Elsődleges rendelési csatorna: B2B portál" and the target document has a section that fully addresses B2B portal ordering
- **THEN** the trace receives status COVERED with a spec_ref pointing to the target section

#### Scenario: Partially covered trace
- **WHEN** a trace states "A visszaigazolásnak figyelembe kell vennie a felületkezelési időt" and the target only mentions lacquering but not staining or oiling
- **THEN** the trace receives status PARTIAL with a note explaining what is missing

#### Scenario: Missing trace
- **WHEN** a trace has no corresponding content in any target document section
- **THEN** the trace receives status MISSING with empty refs

### Requirement: Coverage status values
The system SHALL support exactly these coverage statuses: COVERED, PARTIAL, MISSING, DEFERRED, N/A.

#### Scenario: Deferred trace
- **WHEN** a trace topic is listed in the scope exclusions as M2+
- **THEN** the trace receives status DEFERRED

#### Scenario: Not applicable trace
- **WHEN** a trace is a meta-statement or framing decision that does not need implementable target coverage
- **THEN** the trace receives status N/A

### Requirement: Target section references
Each matched trace SHALL include a reference to the target file and section that covers it. The reference SHALL contain file path, line number, and section identifier.

#### Scenario: Single target reference
- **WHEN** a trace is covered by exactly one target section
- **THEN** refs contains one entry with file, line, and section fields

#### Scenario: Multiple target references
- **WHEN** a trace is covered by content spread across multiple target sections
- **THEN** refs contains multiple entries, one per target section

### Requirement: Modal verb sensitivity
The matching SHALL be sensitive to modal verb distinctions. A trace using "may" (küldhet) SHALL NOT be considered COVERED if the target uses "must" (küld/kell) without acknowledging optionality.

#### Scenario: Modal mismatch detected
- **WHEN** a trace states "A rendszer visszaigazolást küldhet" (may send) and the target states "A rendszer visszaigazolást küld" (sends)
- **THEN** the trace receives status PARTIAL with a note about the modal verb mismatch

### Requirement: Batch matching
The system SHALL batch multiple traces into a single LLM subagent call where possible, rather than making one call per trace.

#### Scenario: Traces batched by target section relevance
- **WHEN** 15 traces need to be matched against 5 target sections
- **THEN** the system makes a small number of batched subagent calls (not 15 individual calls)
