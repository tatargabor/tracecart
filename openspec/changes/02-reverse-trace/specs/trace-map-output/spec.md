## MODIFIED Requirements

### Requirement: Trace-map JSON structure
The trace-map.json output SHALL include a `reverse_traces` section containing target-extracted claims with their traceability status, in addition to the existing `traces` section.

#### Scenario: Reverse traces in output
- **WHEN** the pipeline completes with both forward and reverse matching
- **THEN** trace-map.json contains a `reverse_traces` array with entries structured as: `{id, text, type, source: {file, line}, status, nearest_source_trace, similarity_note}`

#### Scenario: Backward-compatible output
- **WHEN** a consumer reads trace-map.json and does not expect `reverse_traces`
- **THEN** the existing `traces` array and `summary` fields remain unchanged in structure; `reverse_traces` is an additive field

### Requirement: Coverage summary with reverse statistics
The `summary` object in trace-map.json SHALL include reverse trace statistics alongside forward statistics.

#### Scenario: Summary includes reverse stats
- **WHEN** reverse tracing produces 45 target claims of which 42 are traced and 3 are untraced
- **THEN** the summary includes `reverse_total: 45`, `reverse_traced: 42`, `reverse_untraced: 3`, `reverse_coverage_pct: 93.3`

#### Scenario: Reverse coverage score formula
- **WHEN** computing `reverse_coverage_pct`
- **THEN** the formula is `(traced + partial_source × 0.5) / (traced + partial_source + untraced) × 100` — mirroring the forward formula
