## ADDED Requirements

### Requirement: Source fixture document
The test fixtures SHALL include a source document with 15-20 atomic traces in natural text, covering multiple trace types (REQUIREMENT, DECISION, EXCLUSION) and difficulties (explicit, compound, implicit).

#### Scenario: Source contains compound sentences
- **WHEN** the source fixture is processed by clause_split
- **THEN** at least 3 compound sentences are split into multiple clauses

#### Scenario: Source contains implicit traces
- **WHEN** the source fixture is processed by extraction
- **THEN** at least 2 implicit traces are identifiable from word choice

### Requirement: Target fixture document
The test fixtures SHALL include a target document that covers approximately 80% of the source traces, with a known distribution of COVERED, PARTIAL, and MISSING statuses.

#### Scenario: Known coverage distribution
- **WHEN** the fixture target is matched against the fixture source
- **THEN** the resulting coverage is approximately 80% (±5%) with at least 2 PARTIAL and at least 2 MISSING traces

### Requirement: Expected output fixture
The test fixtures SHALL include an expected.json file with the ground truth mapping: which traces exist, which clause_ids they reference, and what coverage status each should receive.

#### Scenario: Ground truth verification
- **WHEN** the pipeline runs on fixture data
- **THEN** the output can be compared against expected.json to verify correctness

### Requirement: Fixture domain
The test fixtures SHALL use the TerraFurn (fictional furniture manufacturer) domain, consistent with the existing benchmark examples.

#### Scenario: Domain consistency
- **WHEN** examining fixture content
- **THEN** all references use TerraFurn domain concepts (wood stock, CNC capacity, finishing, delivery)
