## Context

tracecart has individual Python scripts for clause splitting, document parsing, and input discovery, plus a benchmark framework. The DESIGN.md captures the full architectural vision. This change implements the minimum viable pipeline: source documents in, trace-map.json out.

The runtime is Claude Code — LLM calls happen via subagents, deterministic logic runs as Python scripts invoked from the agent. No external SDK dependencies.

Existing code:
- `src/parse/clause_split.py` — deterministic compound sentence splitter (working, tested)
- `src/parse/parse_document.py` — chapter/section boundary detection (working)
- `src/parse/discover_inputs.py` — find and sort source files chronologically (working)
- `src/extract/remainder.py` — recursive remainder tracker (skeleton, core logic implemented)
- `src/output/trace_map.py` — trace-map.json generator (skeleton, core logic implemented)
- `prompts/extract.txt`, `prompts/verify.txt`, `prompts/coverage_check.txt` — LLM prompt templates (exist for both Hungarian and English)

## Goals / Non-Goals

**Goals:**
- End-to-end pipeline: source docs + target docs → trace-map.json
- Recursive remainder extraction with deterministic termination
- Coverage matching with COVERED/PARTIAL/MISSING/DEFERRED/N/A statuses
- Test fixtures with known coverage for smoke testing
- All deterministic code testable offline (stdin/stdout JSON)
- Runnable from Claude Code without any pip install

**Non-Goals:**
- Topic clustering (v2 — needed at 100+ traces scale)
- Temporal override detection (v2 — needs multi-source time ordering)
- Bidirectional analysis / scope creep detection (see `02-reverse-trace`)
- LSP server / editor integration (`04-lsp-visualization`)
- Benchmark generator (`03-benchmark-suite`)
- Scale beyond ~50 traces (flat matching is O(n×m), acceptable at this size)

## Decisions

### 1. Pipeline orchestration: Claude Code agent, not a Python script

The main loop runs as Claude Code agent logic, not a standalone `run_trace.py` Python script.

**Rationale:** The pipeline interleaves deterministic steps (Python) with LLM calls (subagents). Writing this as a Python script would require the Anthropic SDK. Keeping it as agent logic means zero dependencies — the user just runs the agent.

**Alternative considered:** Standalone Python CLI with Anthropic SDK. Rejected: adds dependency, API key management, and moves away from the "Claude Code is the runtime" architecture.

**Trade-off:** Not runnable outside Claude Code. Acceptable for v1 — CI integration (`05-hook-auto-trace` and beyond) can add SDK support later.

### 2. Extraction: clause_split → subagent → remainder loop

```
source.md
    │
    ▼
clause_split.py (Python, deterministic)
    │ → clauses.json [{clause_id, text, line_number}]
    ▼
subagent: extract traces (LLM)
    │ → traces referencing clause_ids
    ▼
remainder.py (Python, deterministic)
    │ → untraced clauses
    │
    ├── if remainder ≠ ∅ AND remainder shrank:
    │       ▼
    │   subagent: extract from remainder (LLM, different angle)
    │       │
    │       └── loop back to remainder.py
    │
    └── if remainder = ∅ OR didn't shrink:
            ▼
        DONE → all_traces.json
```

**Rationale:** The LLM might miss traces on the first pass (especially implicit ones). The remainder loop catches these without trusting the LLM to self-assess completeness. Termination is deterministic: either all clauses are consumed, or the LLM can't reduce the remainder further.

**Max iterations:** 3 (same as current verify loop). Diminishing returns after 2-3 passes.

### 3. Matching: flat comparison, all traces vs all target sections

For v1, every trace is checked against every target section. No topic-based pre-filtering.

**Rationale:** At 10-50 traces and 5-20 target sections, this is tractable in a single subagent call (or a few batched calls). Topic clustering adds complexity without value at this scale.

**When to revisit:** When benchmark (`03-benchmark-suite`) shows degradation at higher trace counts.

### 4. Subagent prompting: existing prompts with JSON output

Reuse `prompts/extract.txt` for extraction and `prompts/coverage_check.txt` for matching. The `prompts/verify.txt` adversarial pass is folded into the remainder loop — instead of a separate "verify" subagent, we re-extract from the remainder.

**Rationale:** The remainder loop structurally replaces the adversarial verify. Instead of asking "what did I miss?" (LLM might miss again), we ask "extract from these untraced clauses" (fresh context, no priming from previous extraction).

### 5. Test fixtures: hand-crafted TerraFurn domain

Small test corpus in the TerraFurn (fictional furniture manufacturer) domain:
- `tests/fixtures/source.md` — 15-20 traces in natural Hungarian text
- `tests/fixtures/target.md` — covers ~80% of traces (with known COVERED, PARTIAL, MISSING)
- `tests/fixtures/expected.json` — ground truth mapping

**Rationale:** Deterministic, repeatable, no LLM needed to generate. The TerraFurn domain is already established in the benchmark.

## Risks / Trade-offs

**[Risk] LLM output format inconsistency** — Subagent might not return valid JSON or might use unexpected schema.
→ Mitigation: Python validation layer between subagent output and next pipeline step. Log and fail clearly on malformed output.

**[Risk] Remainder loop doesn't converge** — LLM keeps finding 0 new traces but remainder isn't empty.
→ Mitigation: Max 3 iterations hard-coded. Untraceed remainder is logged and surfaced in trace-map.json as `untraced_clauses`.

**[Risk] Flat matching is too slow at scale** — O(n×m) subagent calls.
→ Mitigation: v1 targets 50 traces max. Batch traces into a single subagent prompt where possible. Clustering deferred to v2.

**[Risk] Claude Code context limits** — Large documents might exceed subagent context.
→ Mitigation: Chunk source documents by chapter/section. Process one section at a time. Traces are small (single sentences).
