## 1. Benchmark Generator

- [ ] 1.1 Create trace template library (100+ distinct statement templates in TerraFurn domain)
- [ ] 1.2 Implement `benchmark/generator.py` — deterministic source generation from templates
- [ ] 1.3 Implement coverage selection (random_sample with seed)
- [ ] 1.4 Implement LLM reformulation step (subagent rewrites selected traces into natural target prose)
- [ ] 1.5 Implement ground truth JSON output (trace_id → expected_status mapping)
- [ ] 1.6 Test: generate at all 5 scales (20, 50, 100, 200, 500) and verify ground truth correctness

## 2. Scoring Framework

- [ ] 2.1 Create `benchmark/score_tracemap.py` — compare trace-map.json against ground truth
- [ ] 2.2 Implement metrics: detection recall, gap recall, coverage accuracy, false positive rate, F1
- [ ] 2.3 Implement per-category breakdown (by difficulty tag)
- [ ] 2.4 Implement scale degradation report (markdown table across all scale levels)
- [ ] 2.5 Test: score a perfect trace-map → all metrics 100%

## 3. Model-vs-Tool Comparison

- [ ] 3.1 Create raw LLM baseline runner (sends source+target to LLM with traceability prompt)
- [ ] 3.2 Implement 3 prompt variants for raw LLM (simple list, structured JSON, CoT)
- [ ] 3.3 Implement comparison runner: for each scale × coverage_pct, run both tracecart and raw LLM
- [ ] 3.4 Parse raw LLM output into comparable format (normalize to trace_id → status)
- [ ] 3.5 Generate comparison report (markdown + JSON)

## 4. Stress Tests

- [ ] 4.1 Create compound sentence fixtures (5-10 examples, various conjunction patterns)
- [ ] 4.2 Create implicit trace fixtures (5-10 examples, word choice implications)
- [ ] 4.3 Create modal verb fixtures (5-10 examples, küldhet vs küld patterns)
- [ ] 4.4 Create near-miss distractor fixtures (5-10 examples, topic match but content miss)
- [ ] 4.5 Create keyword distractor fixtures (5-10 examples, same words different meaning)
- [ ] 4.6 Run pipeline on all stress tests, report per-category accuracy

## 5. Publication

- [ ] 5.1 Run full benchmark suite (all scales, all coverage levels)
- [ ] 5.2 Generate publishable results (markdown tables + charts data)
- [ ] 5.3 Write benchmark methodology section for README
