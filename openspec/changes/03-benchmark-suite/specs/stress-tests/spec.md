## ADDED Requirements

### Requirement: Compound sentence stress test
The stress tests SHALL include documents where traces are hidden inside compound sentences that require clause splitting to detect.

#### Scenario: 4-way compound
- **WHEN** a source contains "figyelembe kell vennie a X-t, Y-t, Z-t és W-t"
- **THEN** the tool correctly identifies 4 separate traces, not 1 merged trace

### Requirement: Implicit trace stress test
The stress tests SHALL include documents with implicit traces derivable from word choice but not explicitly stated.

#### Scenario: B2B implies not B2C
- **WHEN** a source mentions "B2B portál" without explicitly stating "not end-consumer"
- **THEN** the tool detects the implicit exclusion trace

### Requirement: Modal verb stress test
The stress tests SHALL include pairs where the source uses "may" (küldhet) but the target uses "must" (küld/kell), requiring PARTIAL not COVERED.

#### Scenario: Modal mismatch detection
- **WHEN** source says "küldhet" and target says "küld"
- **THEN** the tool reports PARTIAL, not COVERED

### Requirement: Near-miss distractor stress test
The stress tests SHALL include target content that mentions the same topic as a source trace but does NOT actually cover the specific point, requiring MISSING not COVERED.

#### Scenario: Topic match but content miss
- **WHEN** source says "delivery must happen on weekdays only" and target says "delivery scheduling is configurable"
- **THEN** the tool reports MISSING or PARTIAL, not COVERED (the constraint is not preserved)

### Requirement: Distractor stress test
The stress tests SHALL include target content that uses the same keywords as a source trace but has a different meaning.

#### Scenario: Same words different meaning
- **WHEN** source says "capacity planning for CNC machines" and target says "CNC machine capacity = 500 units/day" (specific number, different claim)
- **THEN** the tool correctly distinguishes and does not mark as COVERED
