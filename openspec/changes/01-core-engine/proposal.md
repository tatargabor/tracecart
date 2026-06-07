## Why

tracecart currently has individual Python scripts for parsing and a benchmark framework, but no end-to-end pipeline that takes source documents and target documents and produces a coverage report. Without this core pipeline, nothing else (benchmarks, LSP visualization, agent integration) can be built on top.

## Context & Key Decisions

### What tracecart is

A tool that answers: "Given a pile of meetings, emails, and specs that evolved over time — does the final document contain everything, miss nothing, and correctly reflect the latest decisions?"

Two corpora:
- **Source**: time-ordered, potentially unstructured documents (the authoritative input)
- **Target**: structured documents we verify for completeness against the source

### Terminology: "trace"

The atomic unit is called a **trace** — a traceable path from where something was said (source) to where it should be covered (target). Not "claim" (too legal/adversarial), not "requirement" (too narrow — traces include decisions, exclusions, wishes). Types: REQUIREMENT | DECISION | WISH | OPEN_QUESTION | EXCLUSION.

The project name `tracecart` = "set of traces."

### Two-layer architecture

The system has a **deterministic control layer** (Python, set operations, remainder tracking) and a **semantic layer** (LLM via Claude Code subagents). The control layer never trusts the LLM for completeness — it structurally verifies that every input clause has been accounted for.

### Recursive remainder model

Core insight: the LLM is unreliable for knowing when it's "done." Instead of asking "did you miss anything?" (another LLM call that could also miss things), we **deterministically track** which input clauses have been consumed by extracted traces. What remains is the "remainder" — extract again from it until empty or not shrinking.

```
traced + remainder = all_clauses  (invariant at every step)
termination: remainder = ∅ OR remainder didn't shrink
```

### Three-pass extraction quality (from competitor research)

Learned from studying Claimify (Microsoft), FActScore, and MiniCheck:
1. **Disambiguation** (Claimify) — before extraction, flag ambiguous clauses (pronouns, multi-object conjunctions)
2. **Entity check** (FActScore) — after extraction, verify all entities/numbers from source appear in traces. Cheap pre-check before expensive remainder loop
3. **Min-max matching** (MiniCheck) — check traces against individual target sections (not whole doc), take max. Target section as cacheable prompt prefix

### Runtime: Claude Code as the platform

No Anthropic SDK dependency. No pip install (except pygls for LSP later). The agent orchestrates Python scripts (deterministic) and subagents (LLM) interleaved. This means zero setup — but also means it only runs inside Claude Code for now.

### Trace IDs are stable

Format: `T-{source_hash6}-{line}-{clause_index}`. Hash is from file path (not content), so editing a file doesn't change IDs. This enables git-diffing trace-map.json across runs.

### Coverage score: PARTIAL = 0.5

Formula: `(covered + partial × 0.5) / (covered + partial + missing) × 100`. PARTIAL is not the same as COVERED — if everything is PARTIAL, score is 50%, not 100%.

### SUPERSEDED reserved for v2

v1 has no temporal override detection. SUPERSEDED status exists in the schema (forward compat) but is always 0. All traces treated as active.

## What Changes

- Implement the full extraction pipeline: source documents → atomic traces via clause splitting + LLM subagent extraction with recursive remainder tracking
- Implement disambiguation pre-check (ambiguous clauses flagged before extraction)
- Implement entity-based completeness check (deterministic gap detection after extraction)
- Implement the matching pipeline: traces × target document sections → coverage statuses via LLM subagent
- Implement trace-map.json output generation from extraction + matching results
- Create test fixtures (hand-crafted source + target documents with known coverage) for development and smoke testing
- Wire everything into an end-to-end agent workflow runnable from Claude Code
- Phase checkpoints: extraction results saved to disk before matching begins (no re-extraction if matching fails)

This is v1: no topic clustering, no temporal override detection. Flat matching, all traces treated as active. Scale target: 10-50 traces. Bidirectional analysis (reverse trace) is handled by `02-reverse-trace` which builds on top of this.

## Capabilities

### New Capabilities
- `trace-extraction`: Extract atomic traces from source documents using clause splitting + disambiguation + LLM extraction + entity check + recursive remainder tracking for deterministic completeness
- `coverage-matching`: Match extracted traces against target document sections and assign coverage statuses (COVERED/PARTIAL/MISSING/DEFERRED/N/A) with modal verb sensitivity
- `trace-map-output`: Generate the universal trace-map.json format from extraction and matching results, including untraced_clauses and coverage_score_pct
- `test-fixtures`: Hand-crafted source + target document pairs with known coverage for testing (TerraFurn fictional furniture manufacturer domain)

### Modified Capabilities

(none — no existing specs)

## Impact

- `src/extract/`: new extraction pipeline code (remainder.py already has skeleton)
- `src/extract/entity_check.py`: new deterministic entity completeness check
- `src/match/`: new coverage matching module
- `src/output/`: trace_map.py already has skeleton, will be finalized
- `prompts/`: extract.txt and coverage_check.txt are used by subagents
- `tests/fixtures/`: new test data directory
- Dependencies: none added (Python stdlib only, LLM via Claude Code subagents)

## Use Cases This Enables

### Primary: Specification verification feedback loop
An agent writes a spec based on input requirements. tracecart runs source (requirements) vs. target (written spec), reports gaps. Agent iterates until 100% coverage. This is a **live feedback loop** the agent calls during writing, not a post-hoc audit.

### Agent-as-user integration
tracecart is designed to be called by other agents, not just humans. The trace-map.json output is machine-readable — an agent reads it, finds MISSING traces, and fixes them.

### Other use cases
Contract audit (amendments → final), compliance (regulations → policies), decision tracking (meeting notes → decision log), translation QA (original → translation), handover audit.

## Competitor Landscape (what exists, why we're different)

| Tool | What it does | What we learned | What they lack |
|------|-------------|----------------|----------------|
| Claimify (Microsoft) | Atomic claim extraction via Selection→Disambiguation→Decomposition | Disambiguation stage before extraction | No completeness tracking, no remainder |
| MiniCheck (UT Austin) | Claim-document entailment scoring | Min-max chunk aggregation, cacheable prefix | Binary only, no PARTIAL, no traceability |
| FActScore (UW/Meta) | Atomic fact decomposition + verification | Entity-based completeness check, BM25 demo selection | No completeness guarantee, single-pass |
| Factcheck-GPT (MBZUAI) | End-to-end fact-checking pipeline | Check-worthiness classification, stance categories | Uses eval() on LLM output, no remainder tracking |
| TraceLLM (2026 paper) | LLM-based trace link recovery | Prompt engineering strategies | No extraction, no override, not open source |
| Doorstop/StrictDoc | Traditional requirements traceability | Data structures, YAML storage | Manual, no NLP/LLM, no extraction |

**Our unique combination that no competitor has:**
1. Temporal override resolution (later supersedes earlier)
2. Deterministic completeness control (recursive remainder)
3. Three-pass extraction quality (disambiguate + extract + entity check)
4. Bidirectional corpus-to-corpus coverage
5. Editor-native output via LSP (no separate UI)
6. Zero SDK dependency (Claude Code is the runtime)
