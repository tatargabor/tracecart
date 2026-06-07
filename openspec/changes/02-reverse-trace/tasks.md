## 1. Target Extraction

- [ ] 1.1 Verify `clause_split.py` works on target-style documents (structured prose, section headings) — run on an example target and check output
- [ ] 1.2 Add meta-content filtering to extraction: skip section headings, cross-references, table of contents, boilerplate before extraction
- [ ] 1.3 Implement `RT-` prefix ID generation for reverse traces (same algorithm as `T-` but with target file hash)
- [ ] 1.4 Test target extraction on `tests/fixtures/target.md` — verify claims are extracted with correct IDs and clause references

## 2. Reverse Matching

- [ ] 2.1 Add `direction` parameter to matching module: `forward` (existing) or `reverse`
- [ ] 2.2 Create parameterized matching prompt — replace hardcoded "trace"/"target" with `{claim}`/`{evidence}` placeholders, usable in both directions
- [ ] 2.3 Implement reverse matching logic: each target claim checked against source trace set, assign TRACED / PARTIAL_SOURCE / UNTRACED_IN_SOURCE
- [ ] 2.4 Implement "nearest source trace" identification — when status is UNTRACED_IN_SOURCE or PARTIAL_SOURCE, ask LLM for closest source trace and similarity note (piggyback on matching call)
- [ ] 2.5 Test reverse matching on fixtures — create expected reverse results in `tests/fixtures/expected.json` and verify

## 3. Output Extension

- [ ] 3.1 Extend `trace_map.py` to accept `reverse_traces` list and include in output JSON
- [ ] 3.2 Add reverse statistics to `compute_summary()`: `reverse_total`, `reverse_traced`, `reverse_untraced`, `reverse_coverage_pct`
- [ ] 3.3 Extend `build_target_annotations()` to include `UNTRACED_IN_SOURCE` diagnostics for LSP consumption
- [ ] 3.4 Validate output: reverse_traces present, all required fields non-null, reverse_coverage_pct formula correct

## 4. Integration

- [ ] 4.1 Wire reverse extraction + matching into the agent pipeline: after forward matching, run target extraction → reverse matching → merge into trace-map
- [ ] 4.2 End-to-end test: source.md + target.md → trace-map.json with both forward traces and reverse_traces sections
- [ ] 4.3 Verify backward compatibility: existing trace-map consumers (LSP server) handle the new `reverse_traces` field gracefully (ignore if unknown)
