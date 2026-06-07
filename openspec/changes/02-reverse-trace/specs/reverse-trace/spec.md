## ADDED Requirements

### Requirement: Target document claim extraction
The system SHALL extract atomic claims from target documents using the same extraction pipeline as source documents (clause splitting → LLM extraction → recursive remainder tracking).

#### Scenario: Target document extraction
- **WHEN** a target document `design.md` contains compound sentences and implicit claims
- **THEN** the system produces atomic claims with unique IDs (format `RT-{hash6}-{line}-{clause}`) and clause references, identical in structure to source traces

#### Scenario: Extraction pipeline reuse
- **WHEN** the system extracts claims from a target document
- **THEN** it uses the same `clause_split.py`, extraction prompt, and remainder loop as source extraction — no separate extraction codepath

### Requirement: Reverse traceability matching
The system SHALL check each target-extracted claim against the full set of source traces to determine whether the claim is traceable to a source document.

#### Scenario: Fully traceable target claim
- **WHEN** a target claim states "Az elsődleges rendelési csatorna a B2B portál" and a source trace states "Elsődleges rendelési csatorna: B2B portál"
- **THEN** the target claim receives status `TRACED` with a reference to the matching source trace

#### Scenario: Untraced target claim
- **WHEN** a target claim states "Minden rendelés max 48h-n belül visszaigazolásra kerül" and no source trace mentions a 48-hour deadline
- **THEN** the target claim receives status `UNTRACED_IN_SOURCE`

#### Scenario: Partially traceable target claim
- **WHEN** a target claim covers a topic mentioned in source but adds unsupported specifics (e.g., source says "gyors visszaigazolás" but target says "48h-n belül")
- **THEN** the target claim receives status `PARTIAL_SOURCE` with a note explaining what is and is not supported

### Requirement: Nearest source trace identification
When a target claim is `UNTRACED_IN_SOURCE` or `PARTIAL_SOURCE`, the system SHALL identify the most semantically similar source trace, if any exists.

#### Scenario: Close match exists
- **WHEN** a target claim about "48h visszaigazolás" is untraced but source trace T-a3f2c1-047 mentions "gyors visszaigazolás"
- **THEN** the reverse trace includes `nearest_source_trace: "T-a3f2c1-047"` and a `similarity_note` explaining the relationship

#### Scenario: No close match
- **WHEN** a target claim has no semantically related source trace
- **THEN** `nearest_source_trace` is null and `similarity_note` states "no related source trace found"

### Requirement: Meta-content filtering
The extraction SHALL skip meta-content in target documents (section headings, cross-references, table of contents, boilerplate) and only extract substantive claims.

#### Scenario: Heading filtered out
- **WHEN** a target document contains "## 2.2 Rendelési folyamat" as a section heading
- **THEN** the heading is not extracted as a claim

#### Scenario: Cross-reference filtered out
- **WHEN** a target document contains "Lásd: §3.1 Kapacitástervezés"
- **THEN** the cross-reference is not extracted as a claim
