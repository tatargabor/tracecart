## Why

The core engine (`01-core-engine`) produces trace-map.json, but we have no way to measure whether its output is correct. We need:
1. Controlled test data with **known** coverage levels to verify tool correctness
2. A model-vs-tool comparison proving the tool's reason to exist (models lose track at scale)
3. Stress tests for edge cases (compound sentences, implicit traces, modal verbs)

This benchmark suite also becomes a **publishable artifact** — open source model comparison data that demonstrates where each LLM breaks down on traceability tasks. No one has published this data before.

## Context & Key Decisions

### Hypothesis: models lose track at ~50+ items

When a human or LLM reads two documents and tries to match every statement from A to a section in B, they can handle ~20 items easily. At 50, they start missing connections. At 100+, they miss significantly. At 500+, they're essentially guessing.

set-trace solves this by offloading completeness tracking to deterministic code. The model only needs to understand individual statements — it never needs to "hold" the full list in context.

**This benchmark proves this hypothesis quantitatively.** If the hypothesis is wrong, the tool has no reason to exist. If it's right, we have publishable data showing exactly where each model breaks.

### Generator: deterministic skeleton + LLM reformulation

The generator does NOT use LLM to create source traces — traces come from a deterministic template library. LLM is used ONLY to reformulate the target so matching isn't trivial string comparison. This ensures we know ground truth with absolute certainty.

```
Templates (deterministic) → Source document (N traces)
                               ↓
                          Random sample (coverage_pct%)
                               ↓
                          LLM reformulate → Target document (natural prose)
                               ↓
                          Ground truth: {trace_id → COVERED | MISSING}
```

### Why not just use the existing Chapter 9 benchmark?

The existing benchmark (41 ground truth items, 7 methods) measures extraction quality only — which method finds the most requirements from a single document. The new benchmark measures the **full pipeline** (extraction + matching + coverage reporting) against **controlled pairs** at **varying scales**.

### Model-vs-tool: proving our value

Same source+target pair → raw LLM gets the documents + a traceability prompt → set-trace runs its full pipeline → both scored against same ground truth.

We test 3 different prompt variants for the raw LLM and use its **best** result — this makes the comparison conservative (we compete against the raw model's best performance, not a strawman).

Expected results by scale:
- 20 traces: raw LLM ~95%, set-trace ~98% (small difference)
- 50 traces: raw LLM ~85%, set-trace ~96% (gap opens)
- 100 traces: raw LLM ~70%, set-trace ~95% (significant)
- 200 traces: raw LLM ~55%, set-trace ~93% (tool clearly superior)
- 500 traces: raw LLM ~35%, set-trace ~90% (model essentially fails)

These are hypothesized — actual data will tell. Either way, the data is interesting and publishable.

### Multi-model comparison

Run the same benchmark with Claude Opus, Sonnet, Haiku, GPT-4o, etc. This produces a **model capability leaderboard** for document traceability — does Opus hold out longer than Sonnet? Is GPT-4o better or worse at Hungarian text? This data doesn't exist anywhere and would be valuable to the community.

### Stress test categories

| Category | What it tests | Why it matters |
|----------|--------------|---------------|
| Compound sentences | clause_split effectiveness | LLMs merge compound items, our splitter catches them |
| Implicit traces | word choice detection | "B2B" implies not B2C — only found with explicit prompting |
| Modal verbs | küldhet ≠ küld sensitivity | PARTIAL not COVERED — subtle but critical |
| Near-miss distractors | COVERED vs PARTIAL precision | Target mentions topic but misses specific point |
| Keyword distractors | False positive resistance | Same words, different meaning → should be MISSING |
| Override scenarios | Temporal supersession (v2) | Later doc contradicts earlier — future test |

## What Changes

- Build a benchmark generator that creates source+target document pairs with deterministic, known coverage percentages (100%, 75%, 50%, 25%)
- LLM reformulates traces into natural prose (so matching isn't trivial string comparison) while generator controls which traces are included
- Create model-vs-tool benchmark: same task given to raw LLM vs. set-trace, at increasing scales (20, 50, 100, 200, 500 traces)
- Create stress test fixtures: compound sentences, implicit traces, modal verb nuances, near-miss distractors
- Scoring framework that compares tool output against ground truth and reports precision/recall/F1
- Generate publishable results (markdown tables, comparison charts data)

## Capabilities

### New Capabilities
- `benchmark-generator`: Generate source+target document pairs with controlled coverage percentages, using LLM only for reformulation. Deterministic source, deterministic selection, ground truth with certainty.
- `model-comparison`: Run the same traceability task with raw LLM (no tool) and with set-trace, compare against ground truth at multiple scales. Best-of-3 prompts for raw LLM (conservative comparison).
- `stress-tests`: Curated edge-case fixtures testing compound splitting, implicit detection, modal sensitivity, near-miss and keyword distractors
- `scoring-framework`: Score any trace-map.json against ground truth, report detection recall, gap recall, coverage accuracy, false positive rate, F1, per-category breakdown

### Modified Capabilities

(none)

## Impact

- `benchmark/` directory — new generator, scoring, and results
- `tests/stress/` — stress test fixtures
- Depends on: `01-core-engine` must be complete — the benchmark runs the pipeline
- Output: publishable results (markdown tables, JSON data) showing model comparison
- Potential: blog post / paper material on "where LLMs break down on document traceability"
