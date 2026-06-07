## ADDED Requirements

### Requirement: Score trace-map against ground truth
The scoring framework SHALL compare a trace-map.json output against a ground truth JSON and compute accuracy metrics.

#### Scenario: Perfect score
- **WHEN** trace-map.json exactly matches ground truth (all statuses correct)
- **THEN** detection recall = 100%, gap recall = 100%, false positive rate = 0%

#### Scenario: Missed traces
- **WHEN** trace-map marks 5 traces as COVERED that ground truth says are MISSING
- **THEN** false positive rate reflects those 5 errors

### Requirement: Metrics reported
The scoring framework SHALL report: detection recall, gap recall, coverage accuracy (|reported% - actual%|), false positive rate, and F1 score.

#### Scenario: Metrics output
- **WHEN** scoring completes
- **THEN** all 5 metrics are reported as a JSON object

### Requirement: Scale degradation report
The scoring framework SHALL produce a comparison table showing how metrics change across scale levels (20 → 500 traces).

#### Scenario: Degradation visible
- **WHEN** results exist for all scale levels
- **THEN** a markdown table shows metrics per scale level for both set-trace and raw LLM

### Requirement: Per-category breakdown
The scoring framework SHALL break down results by trace difficulty category (explicit, compound, implicit, nuance) when ground truth includes difficulty tags.

#### Scenario: Category breakdown
- **WHEN** ground truth tags traces with difficulty levels
- **THEN** scoring reports separate recall figures per difficulty category
