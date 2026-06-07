## Context

The core engine (`01-core-engine`) produces trace-map.json from source+target documents. We need to verify it works correctly and prove its value over raw LLM usage. The existing `benchmark/score.py` scores extraction methods against ground truth — this change extends that to full pipeline verification.

## Goals / Non-Goals

**Goals:**
- Verify tool correctness: controlled inputs with known outputs
- Prove tool value: quantify where raw LLMs fail without the tool
- Publishable data: model comparison results for open source community
- Reproducible: anyone can re-run the benchmarks

**Non-Goals:**
- Optimizing the pipeline (that's implementation work, not benchmarking)
- Benchmarking speed/cost (focus on accuracy only for now)
- Supporting non-Claude models in v1 (extend later)

## Decisions

### 1. Generator architecture: deterministic skeleton + LLM reformulation

The generator does NOT use LLM to create traces — it generates them deterministically (templates, combinatorics). LLM is used ONLY to reformulate the target document so matching isn't trivial.

```
Generator (deterministic)
    │
    ├─ source.md: N traces from template library
    │   (each trace is a simple, unambiguous statement)
    │
    ├─ coverage_set: random_sample(traces, pct%)
    │   (ground truth: exactly these traces should be COVERED)
    │
    └─ target_raw: selected traces as bullet points
            │
            ▼
        LLM reformulate (subagent)
            │ "Rewrite these points as natural prose paragraphs.
            │  Do not add, remove, or change the meaning."
            ▼
        target.md: natural-sounding document
```

**Why:** If LLM generates the source, we can't know ground truth with certainty. Deterministic source + deterministic selection + LLM-only-for-surface-form gives us certain ground truth.

### 2. Scale progression: 20 → 50 → 100 → 200 → 500

Five scale levels. At each level:
- Generate source with N traces
- Generate 4 targets (100%, 75%, 50%, 25% coverage)
- Run tracecart on each pair
- Run raw LLM on each pair (same task, no tool)
- Score both against ground truth

### 3. Model-vs-tool: identical task, different execution

The raw LLM gets this prompt:
```
Here are two documents. List which statements from Document A 
are covered by Document B. For each, state: COVERED, PARTIAL, or MISSING.
```

tracecart gets the same documents through its full pipeline.

Both outputs scored against the same ground truth. The comparison proves where the tool adds value.

### 4. Scoring metrics

- **Detection recall**: % of known-COVERED traces correctly identified as COVERED
- **Gap recall**: % of known-MISSING traces correctly identified as MISSING  
- **Coverage accuracy**: |reported_pct - actual_pct| (how close is the reported score to reality?)
- **False positive rate**: traces marked COVERED that are actually MISSING
- **Scale degradation**: how metrics change as N increases

### 5. Stress test categories

| Category | What it tests | Example |
|----------|--------------|---------|
| Compound | Clause splitting effectiveness | "figyelembe kell vennie a X-t, Y-t és Z-t" |
| Implicit | Implicit trace detection | "B2B" implying not end-consumer |
| Modal | Modal verb sensitivity | "küldhet" vs "küld" |
| Near-miss | Distinguishing COVERED from PARTIAL | Target mentions topic but misses specific point |
| Distractor | Avoiding false COVERED on superficially similar text | Same keywords, different meaning |
| Override | Temporal supersession (future, for v2) | Later doc contradicts earlier |

## Risks / Trade-offs

**[Risk] LLM reformulation changes meaning** — The reformulated target might accidentally add or remove traces.
→ Mitigation: Validate reformulated target manually for the first few runs. Add a deterministic "meaning preservation check" (entity check: all entities from input appear in output).

**[Risk] Raw LLM comparison is unfair** — Different prompt formulations for the raw LLM might give very different results.
→ Mitigation: Test 3 different prompts (simple list, structured JSON, CoT), report best result for the raw LLM. This makes our comparison conservative (we compare against the raw LLM's best case).

**[Risk] Results vary by run** — LLM outputs are non-deterministic.
→ Mitigation: Run each benchmark 3 times, report mean and standard deviation. Use temperature=0 where supported.
