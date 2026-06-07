## ADDED Requirements

### Requirement: Deterministic source generation
The generator SHALL produce source documents with a known, exact number of atomic traces using template-based generation. No LLM SHALL be used for source creation.

#### Scenario: Generate 100-trace source
- **WHEN** generator is called with n_traces=100
- **THEN** it produces a source document containing exactly 100 distinct, unambiguous statements

### Requirement: Controlled coverage selection
The generator SHALL select a deterministic subset of source traces for coverage, based on a specified percentage and random seed.

#### Scenario: 50% coverage selection
- **WHEN** generator is called with coverage_pct=50 and seed=42
- **THEN** exactly 50 traces are selected for coverage, and the same seed always produces the same selection

### Requirement: LLM reformulation of target
The generator SHALL use an LLM subagent to reformulate the selected traces into natural prose for the target document. The reformulation SHALL preserve meaning while changing surface form.

#### Scenario: Reformulated target is not a copy
- **WHEN** the target is generated from 50 selected traces
- **THEN** no sentence in the target is a verbatim copy of a source trace

#### Scenario: Reformulated target preserves meaning
- **WHEN** the target is generated from 50 selected traces
- **THEN** every selected trace is semantically represented in the target document

### Requirement: Ground truth output
The generator SHALL output a ground truth JSON mapping every source trace to its expected status (COVERED if in selection, MISSING if not).

#### Scenario: Ground truth correctness
- **WHEN** generator runs with 100 traces at 75% coverage
- **THEN** ground truth shows exactly 75 COVERED and 25 MISSING entries

### Requirement: Multiple scale levels
The generator SHALL support generating benchmarks at scales: 20, 50, 100, 200, and 500 traces.

#### Scenario: Scale 500
- **WHEN** generator is called with n_traces=500
- **THEN** it produces a valid source document with 500 distinct traces without duplication or degradation
