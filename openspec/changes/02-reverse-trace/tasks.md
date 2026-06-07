## 1. Target Extraction

- [x] 1.1 Verify `clause_split.py` works on target-style documents (structured prose, section headings) — run on an example target and check output
- [x] 1.2 Add meta-content filtering to extraction: skip section headings, cross-references, table of contents, boilerplate before extraction
- [x] 1.3 Implement `RT-` prefix ID generation for reverse traces (same algorithm as `T-` but with target file hash)
- [x] 1.4 Test target extraction on `tests/fixtures/target.md` — verify claims are extracted with correct IDs and clause references

## 2. Reverse Matching

- [x] 2.1 Add `direction` parameter to matching module: `forward` (existing) or `reverse`
- [x] 2.2 Create parameterized matching prompt — replace hardcoded "trace"/"target" with `{claim}`/`{evidence}` placeholders, usable in both directions
- [x] 2.3 Implement reverse matching logic: each target claim checked against source trace set, assign TRACED / PARTIAL_SOURCE / UNTRACED_IN_SOURCE
- [x] 2.4 Implement "nearest source trace" identification — when status is UNTRACED_IN_SOURCE or PARTIAL_SOURCE, ask LLM for closest source trace and similarity note (piggyback on matching call)
- [x] 2.5 Test reverse matching on fixtures — create expected reverse results in `tests/fixtures/expected.json` and verify

## 3. Output Extension

- [x] 3.1 Extend `trace_map.py` to accept `reverse_traces` list and include in output JSON
- [x] 3.2 Add reverse statistics to `compute_summary()`: `reverse_total`, `reverse_traced`, `reverse_untraced`, `reverse_coverage_pct`
- [x] 3.3 Extend `build_target_annotations()` to include `UNTRACED_IN_SOURCE` diagnostics for LSP consumption
- [x] 3.4 Validate output: reverse_traces present, all required fields non-null, reverse_coverage_pct formula correct

## 4. Integration

- [x] 4.1 Wire reverse extraction + matching into the agent pipeline: after forward matching, run target extraction → reverse matching → merge into trace-map
- [x] 4.2 End-to-end test: source.md + target.md → trace-map.json with both forward traces and reverse_traces sections
- [x] 4.3 Verify backward compatibility: existing trace-map consumers (LSP server) handle the new `reverse_traces` field gracefully (ignore if unknown)
