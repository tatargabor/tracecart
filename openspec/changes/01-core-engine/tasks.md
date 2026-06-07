## 1. Test Fixtures

- [x] 1.1 Create `tests/fixtures/source.md` — 15-20 traces in natural Hungarian text (TerraFurn domain), with compound sentences, implicit traces, and exclusions
- [x] 1.2 Create `tests/fixtures/target.md` — target document covering ~80% of source traces, with known COVERED, PARTIAL, and MISSING distribution
- [x] 1.3 Create `tests/fixtures/expected.json` — ground truth mapping (trace_id → clause_id → status → target ref)
- [x] 1.4 Verify clause_split.py correctly splits the fixture source (run and check output)

## 2. Extraction Pipeline

- [x] 2.1 Create `src/extract/extract.py` — orchestration module: reads clauses JSON, formats prompt, calls subagent, parses JSON response, returns traces
- [x] 2.2 Implement extraction loop in agent: clause_split → extract → remainder → re-extract → terminate
- [x] 2.3 Add JSON validation for subagent output (reject malformed, log errors)
- [x] 2.4 Test extraction on fixtures — verify traces reference correct clause_ids

## 3. Coverage Matching

- [x] 3.1 Create `src/match/coverage.py` — reads traces JSON + target document, formats coverage_check prompt, calls subagent, parses response
- [x] 3.2 Implement batched matching — group traces into manageable batches for subagent calls
- [x] 3.3 Add coverage status validation (only COVERED/PARTIAL/MISSING/DEFERRED/N/A accepted)
- [x] 3.4 Test matching on fixtures — verify statuses match expected.json

## 4. Output Generation

- [x] 4.1 Finalize `src/output/trace_map.py` — wire up to produce complete trace-map.json from extraction + matching results
- [x] 4.2 Add untraced_clauses to trace-map output (from remainder tracker)
- [x] 4.3 Validate output: JSON parseable, all required fields present, coverage_score_pct correct

## 5. End-to-End Integration

- [x] 5.1 Create agent workflow: source.md + target.md → trace-map.json (full pipeline in one run)
- [x] 5.2 Run end-to-end on fixtures, compare output against expected.json
- [x] 5.3 Document usage in CLAUDE.md (how to run the pipeline)
