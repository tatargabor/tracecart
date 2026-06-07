# Benchmarks

Extraction method comparison on a Hungarian ERP specification (41-item ground truth).

## Methods tested

| Method | Approach |
|--------|----------|
| A: Single-pass | One LLM call on full text |
| B: Section-by-section | LLM called per section |
| C: Extract + Adversarial Verify | Extract then adversarial review |
| D: Hierarchical | Multi-level decomposition |
| E: Line-anchored | Extraction with line references |
| F: 3-agent union | Union of 3 independent extractions |
| G: Clause-split + anchor + verify | Deterministic split → anchored extract → verify |

## Results

| Method | Detection | Atomic Recall | Precision | F1 |
|--------|-----------|---------------|-----------|-----|
| A: Single-pass | 93% | 73% | 100% | 85% |
| B: Section-by-section | 93% | 83% | 100% | 91% |
| C: Extract + Adversarial Verify | 98% | 93% | 100% | 96% |
| D: Hierarchical | 90% | 80% | 100% | 89% |
| E: Line-anchored | 93% | 78% | 100% | 88% |
| F: 3-agent union | 100% | 85% | 70% | 77% |
| **G: Clause-split + anchor + verify** | **100%** | **93%** | **98%** | **95%** |

## Why Method G wins

Method G (used in production) achieves **100% detection recall** by combining:

1. **Deterministic clause splitting** — eliminates compound sentence problem; every clause gets a stable ID
2. **Line-anchored extraction** — LLM must cite clause IDs, giving mechanical coverage guarantee
3. **Remainder loop** — uncovered clauses are re-submitted (max 3 iterations), ensuring nothing is missed
4. **Validation** — extracted traces are validated against the clause map; invalid types/missing fields are caught

## Metrics definitions

- **Detection**: percentage of ground-truth items that have at least one matching extraction
- **Atomic Recall**: percentage of atomic sub-claims within ground-truth items that are captured
- **Precision**: percentage of extractions that correspond to real requirements (not hallucinated)
- **F1**: harmonic mean of Atomic Recall and Precision

## Ground truth

Located in `benchmark/` (when present). Ground truth is manually verified — never auto-generated.

Each ground-truth entry specifies:
- The requirement text
- Source location (line, clause)
- Difficulty level (1–4)
- Expected trace type

## Running benchmarks

```bash
# Score a method result against ground truth
# (requires benchmark/ directory with ground-truth data)
set-trace score benchmark/ground-truth.json benchmark/method-g.json
```

> Note: The benchmark scoring command is planned but not yet implemented in the TypeScript version. The Python benchmark scripts are preserved in git history.
