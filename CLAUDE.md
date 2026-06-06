# set-trace — Spec Traceability Tool

## What this is

LLM-powered specification traceability. Takes input documents (client specs, meetings, emails), extracts atomic requirements sentence-by-sentence, and verifies coverage against implementation specs. Outputs annotated markdown viewable in Obsidian.

## Architecture

Hybrid: Python for deterministic steps, LLM (Claude) for semantic analysis.

| Component | Type | Purpose |
|-----------|------|---------|
| `src/parse_spec.py` | Python | Chapter boundary detection in spec documents |
| `src/discover_inputs.py` | Python | Find and sort input files chronologically |
| `src/clause_split.py` | Python | Split compound sentences before LLM sees them |
| `src/annotate_markdown.py` | Python | Generate Obsidian-compatible annotated output |
| `prompts/extract.txt` | Prompt | Method G: line-anchored requirement extraction |
| `prompts/verify.txt` | Prompt | Adversarial verification (loop until dry) |
| `prompts/coverage_check.txt` | Prompt | Sentence-vs-spec coverage matching |

## Key method: Method G (Clause-split + Line-anchor + Verify)

This achieves 100% detection recall on our benchmark:
1. **Clause-split** (deterministic) — compound sentences broken into atomic clauses
2. **Line-anchored extraction** (LLM) — every clause gets a line ref, uncited lines flagged
3. **Adversarial verify** (LLM) — second pass re-reads word-by-word for gaps
4. **Loop until dry** — repeat verify until no new items found (max 3 rounds)

## Running tests

```bash
# Benchmark: scores all 7 methods against ground truth
python3 benchmark/score.py benchmark/chapter9-ground-truth.json benchmark/method-*.json

# Test clause splitter on any text
echo "text here" | python3 src/clause_split.py - --stats

# Test spec parser
python3 src/parse_spec.py path/to/spec.md
```

## Development conventions

- Python 3.11+, no external dependencies beyond standard library
- LLM calls go through Claude Code subagents (not Anthropic SDK directly)
- All outputs must be git-friendly (markdown, JSON — no binary)
- Prompt templates in `prompts/` — keep them as plain text files
- Benchmark ground truth is manually verified — don't auto-generate GT
- Tests should be deterministic where possible; LLM-dependent tests should have cached expected outputs

## Pipeline phases

```
Phase 0: PARSE (deterministic)   — parse_spec.py + discover_inputs.py + clause_split.py
Phase 1: EXTRACT (LLM)           — prompts/extract.txt + prompts/verify.txt
Phase 2: OVERRIDE MAP (det+LLM)  — triple comparison + LLM override classification
Phase 3: VERIFY (LLM)            — prompts/coverage_check.txt
Phase 4: ANNOTATE (deterministic) — annotate_markdown.py
```

## What's NOT built yet (roadmap)

- [ ] `cache_manager.py` — incremental processing (SHA-256 hash based)
- [ ] `override_map.py` — multi-input override detection
- [ ] `run_trace.py` — CLI entry point with --chapters, --input, --specs, --diff flags
- [ ] `prompts/override_detect.txt` — override classification prompt
- [ ] Test suite beyond benchmark (pytest)
- [ ] CI integration (standalone script mode with Anthropic SDK)
