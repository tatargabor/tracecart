# set-trace

LLM-powered specification traceability — sentence-level coverage verification for specs.

**The problem:** You have input specifications (client specs, meeting notes, emails) and generated implementation specs. How do you know the implementation specs cover everything? Manual review misses things — especially implicit requirements, compound sentences, and cross-document overrides.

**set-trace** extracts atomic requirements from inputs, detects contradictions/overrides across documents, and verifies each sentence against your specs. Output: annotated markdown showing exactly what's covered, what's missing, and what was overridden.

## How it works

```
INPUTS (spec docs, meetings, emails)
  → Phase 0: Parse + clause-split (deterministic Python)
  → Phase 1: Extract requirements with triples (LLM)
  → Phase 2: Override detection across inputs (deterministic + LLM)
  → Phase 3: Verify each sentence against specs (LLM)
  → Phase 4: Generate annotated markdown (deterministic Python)
```

Hybrid architecture: Python handles parsing, splitting, formatting, caching. LLM handles semantic extraction, verification, and override classification.

## Benchmark

Tested 7 extraction methods on a 41-item ground truth (Hungarian ERP specification):

| Method | Detection | Atomic Recall | Precision | F1 |
|--------|-----------|---------------|-----------|-----|
| A: Single-pass | 93% | 73% | 100% | 85% |
| B: Section-by-section | 93% | 83% | 100% | 91% |
| C: Extract + Adversarial Verify | 98% | 93% | 100% | 96% |
| D: Hierarchical | 90% | 80% | 100% | 89% |
| E: Line-anchored | 93% | 78% | 100% | 88% |
| F: 3-agent union | 100% | 85% | 70% | 77% |
| **G: Clause-split + anchor + verify** | **100%** | **93%** | **98%** | **95%** |

Method G (used in production) achieves **100% detection recall** by combining:
1. Deterministic clause splitting (eliminates compound sentence problem)
2. Line-anchored extraction (mechanical coverage guarantee)
3. Adversarial verification (catches implicit requirements)

## Output format

Annotated markdown with Obsidian-compatible callout blocks:

```markdown
elsődleges rendelési csatorna: B2B webshop

> [!trace-covered]
> ✅ `CS-9-001` B2B webshop elsődleges csatorna — *01-order-intake.md §2.1*

szállítási idő figyelembevétele

> [!trace-missing]
> ⬜ `CS-9-016` Szállítási idő számítás — nincs spec lefedettség
```

Coverage markers: ✅ COVERED, ⚠️ PARTIAL, ⬜ MISSING, ⏭️ DEFERRED, ➡️ SUPERSEDED, ⚡ CONFLICT

## Quick start

```bash
# Parse a spec into chapters
python3 src/parse_spec.py your-spec.md > chapters.json

# Clause-split a chapter
python3 src/clause_split.py chapter-text.md > clauses.json

# Run the benchmark
python3 benchmark/score.py benchmark/chapter9-ground-truth.json benchmark/method-*.json
```

For the full pipeline (extraction + verification + annotation), use the Claude Code skill `/set:trace-run` — it orchestrates Python scripts and LLM subagents.

## Project structure

```
src/                    # Core Python scripts (deterministic)
  parse_spec.py         # Chapter boundary detection
  discover_inputs.py    # Input file discovery + chronological sorting
  clause_split.py       # Compound sentence splitting + line numbering
  annotate_markdown.py  # Annotated markdown generator (Obsidian callouts)
  format_output.py      # Coverage matrix formatter

prompts/                # LLM prompt templates
  extract.txt           # Method G: line-anchored extraction
  verify.txt            # Adversarial verification
  coverage_check.txt    # Sentence-vs-spec matching

benchmark/              # Ground truth + method comparison
  chapter9-ground-truth.json  # 41 requirements, 4 difficulty levels
  method-a..g.json      # 7 method results with GT mappings
  score.py              # Benchmark scoring script

examples/               # Example outputs
  chapter-09-annotated.md     # Real annotated output from first live run
  obsidian-snippet.css        # Obsidian CSS for coverage callout colors
```

## Language support

Currently tested with Hungarian specifications. The LLM handles language-specific extraction; the deterministic scripts are language-agnostic. Should work with any language Claude supports.

## License

MIT
