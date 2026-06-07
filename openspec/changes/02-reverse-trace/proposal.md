## Why

The 01-core-engine change only implements forward trace (source→target: "did the target cover everything from the source?"). But during matching, the pipeline already iterates over target sections — detecting claims in the target that trace back to NO source is practically free. Without reverse trace, the tool is half-blind: it finds what's missing from the target, but cannot detect hallucinations or unsupported claims the LLM added. This is critical for the hook-based automatic verification use case where set-trace acts as an invisible quality gate.

## What Changes

- Add reverse trace extraction: extract atomic claims from target documents using the same extraction pipeline
- Add reverse matching: check each target-extracted claim against source traces for traceability
- Introduce `UNTRACED_IN_SOURCE` status for target claims that cannot be traced back to any source document
- Extend `trace-map.json` output to include a `reverse_traces` section with untraced target claims
- Extend coverage summary with reverse trace statistics

## Capabilities

### New Capabilities

- `reverse-trace`: Extract claims from target documents and verify they are traceable back to source documents. Claims not traceable to any source receive `UNTRACED_IN_SOURCE` status. This enables hallucination detection and scope creep identification.

### Modified Capabilities

- `coverage-matching`: Add reverse matching direction (target→source) alongside existing forward matching (source→target)
- `trace-map-output`: Extend trace-map.json schema with `reverse_traces` section and reverse coverage statistics

## Impact

- `src/extract/`: reuse existing extraction pipeline on target documents (no new extraction code, just invoked on different input)
- `src/match/`: new reverse matching logic (same entailment check, reversed direction)
- `src/output/trace_map.py`: extended output schema with `reverse_traces` and updated summary
- `prompts/`: may need a reverse-matching prompt variant (or reuse coverage_check.txt with swapped roles)
- `trace-map.json` schema: breaking for consumers that don't expect `reverse_traces` field (additive, so backward-compatible if consumers ignore unknown fields)
- LSP server: can visualize `UNTRACED_IN_SOURCE` as info-level diagnostics on target files
