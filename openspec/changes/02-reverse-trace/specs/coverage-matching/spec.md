## MODIFIED Requirements

### Requirement: Trace-to-target matching
The system SHALL support bidirectional matching: forward (source traces against target sections) and reverse (target claims against source traces). The matching direction SHALL be parameterized, not hardcoded.

#### Scenario: Forward matching (existing behavior)
- **WHEN** matching direction is `forward`
- **THEN** each source trace is compared against target document sections and assigned a coverage status (COVERED/PARTIAL/MISSING/DEFERRED/N/A)

#### Scenario: Reverse matching (new)
- **WHEN** matching direction is `reverse`
- **THEN** each target claim is compared against the full set of source traces and assigned a traceability status (TRACED/PARTIAL_SOURCE/UNTRACED_IN_SOURCE)

#### Scenario: Prompt role swapping
- **WHEN** matching direction is `reverse`
- **THEN** the matching prompt uses the target claim as the "claim to verify" and source traces as the "evidence to check against" — same entailment logic, swapped roles

### Requirement: Batch matching
The system SHALL batch multiple traces into a single LLM subagent call where possible, rather than making one call per trace.

#### Scenario: Reverse traces batched
- **WHEN** 20 target claims need to be matched against source traces
- **THEN** the system makes a small number of batched subagent calls (not 20 individual calls)
