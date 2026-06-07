## ADDED Requirements

### Requirement: Raw LLM baseline
The system SHALL run the same source+target pair through a raw LLM (no tool pipeline) with a standardized traceability prompt, and collect its coverage assessment.

#### Scenario: Raw LLM receives same task
- **WHEN** a benchmark pair is evaluated
- **THEN** the raw LLM receives both documents and the prompt "List which source statements are covered by the target document" and returns its assessment

### Requirement: Multiple prompt variants
The raw LLM baseline SHALL be tested with at least 3 different prompt formulations to find its best-case performance. The best result SHALL be used for comparison (conservative for us).

#### Scenario: Best-of-3 prompts
- **WHEN** raw LLM is evaluated
- **THEN** three different prompts are tested and the highest-scoring result is reported

### Requirement: Scale progression comparison
The comparison SHALL run at each scale level (20, 50, 100, 200, 500 traces) and report metrics for both set-trace and raw LLM at each level.

#### Scenario: Breakpoint identification
- **WHEN** results are collected across all scales
- **THEN** the report identifies the scale at which set-trace first outperforms the raw LLM by >10% on detection recall

### Requirement: Results reproducibility
Each benchmark run SHALL use a fixed random seed and record the model version used. Results SHALL be reproducible by re-running with the same parameters.

#### Scenario: Reproducible results
- **WHEN** the same benchmark is run twice with the same seed and model
- **THEN** the ground truth and source/target documents are identical (LLM outputs may vary slightly)

### Requirement: Multi-model support
The comparison framework SHALL support running against different models (Claude Opus, Sonnet, Haiku, GPT-4o) with results stored per-model.

#### Scenario: Add new model
- **WHEN** a new model is added to the comparison
- **THEN** it can be benchmarked using the same generated test data without regeneration
