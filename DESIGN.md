# tracecart — Design Document

## Project Goal

Extract atomic traces from time-ordered natural language documents, resolve temporal overrides, and verify complete coverage against a target corpus. Provide editor-native visualization via LSP.

**One sentence:** "Given a pile of meetings, emails, and specs that evolved over time — does the final document contain everything, miss nothing, and correctly reflect the latest decisions?"

## Problem Statement

Organizations produce requirements, decisions, and constraints across many documents over time. Later documents override earlier ones. A final "target" document (spec, contract, policy) must fully cover all valid traces. Manually checking this is:
- Error-prone (humans miss compound sentences, implicit requirements, modal verb nuances)
- Time-consuming (hundreds of traces × dozens of target sections)
- Not repeatable (different reviewers find different gaps)

## Core Concepts

### Two corpora

| Corpus | Role | Properties |
|--------|------|------------|
| **Source** | Authoritative input | Time-ordered, potentially unstructured, overrides possible |
| **Target** | Verified for completeness | Structured, the "final product" we're checking |

### Traces

A **trace** is an atomic assertion extracted from the source corpus and tracked through to the target. It is the fundamental unit of traceability — a traceable path from "where it was said" to "where it should be covered."

**Types:** REQUIREMENT | DECISION | WISH | OPEN_QUESTION | EXCLUSION

**Properties:**
- Traced to a specific source location (file:line)
- Tagged by domain topic (for clustering)
- May be implicit (derived from word choice, not explicitly stated)
- Has a semantic triple (subject-attribute-object) for deterministic matching

### Coverage statuses

| Status | Meaning | Available in |
|--------|---------|-------------|
| COVERED | Target fully addresses this specific trace | v1 |
| PARTIAL | Target addresses part but misses something | v1 |
| MISSING | Not addressed in target | v1 |
| DEFERRED | Explicitly out of scope (acknowledged, not forgotten) | v1 |
| N/A | Meta-statement that doesn't need target coverage | v1 |
| SUPERSEDED | Overridden by a later source document | v2 (reserved in v1, always 0) |

### Trace IDs

Format: `T-{source_hash6}-{line}-{clause_index}`

Example: `T-a3f2c1-047-2` (file hash a3f2c1, line 47, 2nd clause)

**Stability:** IDs are deterministic — same input produces same IDs. This enables git diffing of trace-map.json across runs. The 6-char file hash is derived from the source file path (not content), so renaming a file changes IDs but editing content does not.

## Architecture

### Two layers

```
┌─────────────────────────────────────────┐
│  CONTROL LAYER (deterministic)          │
│                                         │
│  - Set operations (∩, \, ⊆)            │
│  - Remainder tracking                   │
│  - Termination conditions               │
│  - Override resolution (temporal)        │
│  - Topic clustering aggregation         │
│  - Output generation (trace-map.json)   │
├─────────────────────────────────────────┤
│  SEMANTIC LAYER (LLM via subagents)     │
│                                         │
│  - Text → atomic traces (extraction)    │
│  - "Does A cover B?" (entailment)       │
│  - "Does B override A?" (supersession)  │
│  - Disambiguation (ambiguity detection) │
│  - Topic assignment (clustering)        │
└─────────────────────────────────────────┘
```

The control layer never trusts the LLM for completeness — it tracks what's been processed and what remains, deterministically.

### Recursive remainder model

The LLM is unreliable for knowing when it's "done." The control layer enforces completeness:

```
function extract_all(clauses):
    traced = {}
    remainder = clauses

    while remainder ≠ ∅:
        new_traces = LLM_extract(remainder)
        consumed = clauses referenced by new_traces
        traced = traced ∪ new_traces
        remainder = remainder \ consumed

        if consumed = ∅:  # LLM found nothing new
            break         # terminate (remainder logged as untraced)

    return traced, remainder
```

**Key insight:** Termination is not "LLM says it's done" but "no untraced input remains" or "LLM cannot reduce remainder further." Untraced remainder is explicitly surfaced as potential gaps.

### Three-pass extraction quality (learned from competitors)

Quality improvements adopted from Claimify and FActScore:

```
Phase 1a: DISAMBIGUATE (LLM, selective)
    For clauses with pronouns, demonstratives, or ambiguous conjunctions:
    → "Is the referent unambiguous?" If not → flag as AMBIGUOUS
    Only ~10-15% of clauses need this check.

Phase 1b: EXTRACT (LLM)
    Standard extraction from clauses → traces

Phase 1c: ENTITY CHECK (deterministic)
    Extract named entities/numbers/dates from source clause.
    Verify each appears in at least one extracted trace.
    Missing entity → flag gap BEFORE expensive remainder loop.

Phase 1d: REMAINDER LOOP (deterministic + LLM)
    Standard recursive remainder on untraced clauses.
```

### Agent orchestration

The pipeline is orchestrated by a Claude Code agent. Data flows between steps via JSON files:

```
Agent
  ├─ run: clause_split.py source.md > clauses.json
  ├─ run: disambiguate subagent (on ambiguous clauses only)
  ├─ run: extract subagent(clauses.json) > traces-raw.json
  ├─ run: entity_check.py(clauses.json, traces-raw.json) > gaps.json
  ├─ if gaps: run extract subagent on gaps
  ├─ run: remainder.py(clauses.json, traces.json) > remainder.json
  ├─ while remainder not empty and shrinking:
  │     run: extract subagent(remainder) > more-traces.json
  │     merge into traces.json
  │     run: remainder.py again
  ├─ SAVE traces.json to disk (phase checkpoint)
  ├─ run: coverage subagent(traces.json, target.md) > matches.json
  ├─ run: trace_map.py(traces.json, matches.json) > trace-map.json
  └─ done
```

**Phase checkpoints:** After extraction completes, traces.json is saved to disk. If matching fails or is interrupted, extraction does not need to re-run.

**Error handling:**
- Subagent returns invalid JSON → log error, retry once with stricter prompt, fail if still invalid
- Subagent returns traces without clause_id → reject those traces, they don't count toward consumed clauses
- Partial failure → save whatever completed to disk, report what failed

### Runtime model

```
┌─────────────────────────────────────────────────┐
│  CLAUDE CODE (interactive agent)                 │
│                                                  │
│  ┌───────────────────┐  ┌───────────────────┐   │
│  │ Python scripts    │  │ Subagents (LLM)   │   │
│  │ (deterministic)   │  │ (semantic layer)  │   │
│  │                   │  │                   │   │
│  │ • clause_split    │  │ • disambiguate    │   │
│  │ • entity_check    │  │ • extract traces  │   │
│  │ • remainder_track │  │ • verify coverage │   │
│  │ • topic_cluster   │  │ • override detect │   │
│  │ • trace_map_gen   │  │ • match traces    │   │
│  └───────────────────┘  └───────────────────┘   │
│                                                  │
│  No SDK dependency. No pip install anthropic.    │
│  Claude Code IS the runtime.                     │
└─────────────────────────────────────────────────┘
```

### Output: trace-map.json

Universal output format consumed by the LSP server and any other visualization:

```json
{
  "version": 1,
  "generated": "2026-06-07T14:30:00Z",
  "source_files": ["meetings/2024-01-15.md", "emails/2024-03-02.md"],
  "target_files": ["specs/order-intake.md", "specs/confirmation.md"],
  "traces": [
    {
      "id": "T-a3f2c1-047-0",
      "text": "A visszaigazolásnak figyelembe kell vennie a CNC kapacitást",
      "type": "REQUIREMENT",
      "source": {"file": "meetings/2024-01-15.md", "line": 47, "col_start": 0, "col_end": 62},
      "triple": {"subject": "visszaigazolás", "attribute": "figyelembe veszi", "object": "CNC kapacitás"},
      "topics": ["manufacturing", "orders"],
      "implicit": false,
      "status": "COVERED",
      "refs": [
        {"file": "specs/confirmation.md", "line": 23, "section": "§2.2"}
      ],
      "override": null
    }
  ],
  "untraced_clauses": [],
  "summary": {
    "total": 142,
    "covered": 98,
    "partial": 22,
    "missing": 15,
    "deferred": 5,
    "superseded": 0,
    "na": 2,
    "coverage_score_pct": 88.9
  }
}
```

**Coverage score formula:** `(covered + partial × 0.5) / (covered + partial + missing) × 100`

PARTIAL counts as half — 20 PARTIAL + 0 COVERED + 0 MISSING = 50%, not 100%. DEFERRED, N/A, and SUPERSEDED are excluded from the denominator.

### Visualization: LSP Server

No custom editor. An LSP server reads `trace-map.json` and provides:

| LSP Feature | Purpose |
|-------------|---------|
| Diagnostics | Color sentences by status (error=missing, warning=partial, hint=covered) |
| Go to Definition | Source trace → jump to target section |
| Find References | Target section → list all source traces it covers |
| Code Lens | Inline summary above sections ("8 traces, 6 covered") |

**Primary editor: Zed** (native LSP support, fast, modern)
**Secondary: VS Code** (once Zed version works)

Any LSP-compatible editor works: Neovim, Emacs, Sublime, etc.

## Pipeline

```
Phase 0: PARSE (deterministic)
    Input:  raw source documents
    Output: numbered clauses per document
    Tools:  clause_split.py, parse_document.py, discover_inputs.py

Phase 1: EXTRACT (LLM + deterministic control)
    Input:  numbered clauses
    Steps:  disambiguate → extract → entity check → remainder loop
    Output: atomic traces with source references
    Checkpoint: traces.json saved to disk after this phase
    Tools:  subagents + prompts/extract.txt + remainder.py + entity_check.py

Phase 2: CLUSTER (deterministic + LLM assist)
    Input:  flat list of traces
    Output: topic-grouped traces
    Method: LLM assigns topics, grouping is deterministic
    Purpose: makes Phase 4 matching tractable at scale

Phase 3: OVERRIDE (deterministic + LLM)
    Input:  time-ordered traces within same topic
    Output: traces with override annotations (SUPERSEDED / ACTIVE)
    Method: within each topic group, compare traces from different time periods
    Tools:  triple comparison (det) + LLM for ambiguous cases

Phase 4: MATCH (LLM + deterministic control)
    Input:  active traces + target document sections
    Output: trace → target section mappings with status
    Method: per-section checking with max aggregation (MiniCheck pattern)
    Control: target section as cacheable prompt prefix, trace as varying suffix
    Tools:  subagent + prompts/coverage_check.txt

Phase 5: OUTPUT (deterministic)
    Input:  full trace map with statuses and references
    Output: trace-map.json
    Tools:  trace_map.py
```

## Scale Considerations

- 50-200 source documents
- 500-2000 atomic traces after extraction
- 10-50 target documents with 100-500 sections
- Topic clustering reduces matching from O(n×m) to O(k × n/k × m/k)

## Differentiators (vs. existing tools)

1. **Temporal override resolution** — no other tool handles "later supersedes earlier"
2. **Deterministic completeness control** — recursive remainder, not "LLM says done"
3. **Three-pass extraction quality** — disambiguate + extract + entity check before remainder loop
4. **Bidirectional** — source→target (coverage) + target→source (scope creep)
5. **No SDK dependency** — runs as Claude Code agent, zero setup
6. **Editor-native output** — LSP, not a separate UI to maintain
7. **Language-aware clause splitting** — deterministic compound sentence splitting before LLM sees text

## Visualization Research (why LSP, not custom UI)

We evaluated 8 visualization approaches for the source↔target mapping problem:

| Approach | Verdict | Reason |
|----------|---------|--------|
| Meld-style bipartite side-by-side | Rejected at scale | 500+ traces → spaghetti connections, unreadable |
| Sankey/alluvial diagram | Dashboard only | Loses individual trace text, good for aggregate overview |
| Coverage heatmap/matrix | Good complement | Compact, scalable, but loses document context |
| Obsidian annotated markdown | Rejected as primary | Link-soup at scale, graph view = hairball at 500+ nodes |
| Force-directed graph | Rejected | Destroys document ordering, chaos at scale |
| Hierarchical drill-down (topic→traces→detail) | Future option | Scales well but needs custom web UI to maintain |
| Radar chart per domain tag | Dashboard widget | Summary only, not for auditing |
| **LSP in editor (code coverage analogy)** | **Chosen** | Zero custom UI, universal (any editor), familiar pattern |

**Key insight:** The problem is identical to code coverage visualization. Istanbul produces coverage.json → editor extension colors lines. We produce trace-map.json → LSP server colors sentences. The editor IS the visualization.

**At scale (500+ traces):** The editor view still works — each file only shows its own traces. The complexity is distributed across files rather than shown all at once. For aggregate views, the trace-map.json summary provides numbers. Future: hierarchical HTML viewer for cross-document overview.

## Technology Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Deterministic logic | Python 3.11+ | No deps, testable, stdin/stdout JSON |
| LLM calls | Claude Code subagents | No SDK, no API keys to manage |
| Output format | JSON (trace-map.json) | Universal, editor-agnostic |
| Visualization | LSP server (Python, pygls) | Works in any editor |
| Primary editor | Zed | Fast, modern, native LSP |
| Version control | Git | Outputs are git-friendly text |

## 3rd Party References

Downloaded to `3rdparty/` for learning:

| Tool | What to learn from it |
|------|----------------------|
| Claimify | Disambiguation stage before extraction (Selection → Disambiguation → Decomposition) |
| MiniCheck | Min-max chunk aggregation for matching, cacheable prompt prefix pattern |
| FActScore | Entity-based completeness check after extraction, BM25 demo selection |
| OpenFactVerification (Loki) | Multi-step verification pipeline design |
| Doorstop | Traceability data structures, YAML-based requirement storage |
| Factcheck-GPT | Check-worthiness classification, stance detection categories. Avoid: eval() on LLM output |

## File Structure (planned)

```
tracecart/
├── DESIGN.md                    # this document
├── CLAUDE.md                    # dev instructions for Claude Code
├── src/
│   ├── parse/
│   │   ├── clause_split.py      # deterministic sentence splitting
│   │   ├── parse_document.py    # chapter/section boundary detection
│   │   └── discover_inputs.py   # find and sort source files
│   ├── extract/
│   │   ├── remainder.py         # recursive remainder tracker
│   │   ├── entity_check.py      # deterministic entity completeness check
│   │   └── triple.py            # subject-attribute-object extraction
│   ├── cluster/
│   │   └── topic_group.py       # topic assignment + grouping
│   ├── override/
│   │   └── temporal.py          # time-based override detection
│   ├── match/
│   │   └── coverage.py          # trace-target matching logic
│   └── output/
│       └── trace_map.py         # generate trace-map.json
├── lsp/
│   └── server.py                # LSP server (pygls)
├── prompts/
│   ├── extract.txt              # trace extraction prompt (Hungarian)
│   ├── verify.txt               # adversarial verify prompt
│   ├── coverage_check.txt       # coverage matching prompt
│   └── en/                      # English equivalents
├── benchmark/
│   ├── chapter9-ground-truth.json
│   ├── method-*.json
│   ├── score.py
│   └── en/
├── 3rdparty/                    # reference implementations (git-ignored)
└── .gitignore
```

## Benchmark Strategy

### 1. Coverage-level benchmarks (tool correctness)

Controlled test documents with **known** coverage percentages. The tool must report the correct coverage level.

**How it works:**
1. A **generator** creates deterministic source+target document pairs
2. Source: N atomic traces (e.g., 100 simple, unambiguous sentences)
3. Target: reformulated versions of a controlled subset (100%, 75%, 50%, 25%)
4. LLM is used ONLY to rephrase/reformulate traces into natural target prose (so matching isn't trivial string comparison)
5. Ground truth is deterministic (the generator knows exactly which traces are covered)

**What we measure:**
- Does the tool correctly identify COVERED traces? (no false negatives)
- Does the tool correctly identify MISSING traces? (no false positives)
- Does the reported coverage % match the actual %?
- At what scale does accuracy degrade? (100 traces? 500? 1000?)

**Generator design:**
```
generate_benchmark(n_traces=100, coverage_pct=50):
    source_traces = generate_n_distinct_traces(n)
    covered_set = random_sample(source_traces, pct=coverage_pct)
    target_doc = LLM_reformulate(covered_set)  # rephrase, don't copy
    ground_truth = {trace.id: trace in covered_set for trace in source_traces}
    return source_doc, target_doc, ground_truth
```

### 2. Model-vs-tool benchmark (proving our value)

Measure how well a raw LLM (without the tool) can find all connections between two documents. This proves that beyond ~50 traces, a model alone loses track.

**Method:**
1. Give the same source+target pair to a raw LLM with the prompt: "List which source statements are covered by the target document"
2. Run the same pair through tracecart
3. Compare both against ground truth
4. Repeat at increasing scales: 20, 50, 100, 200, 500 traces

**Expected result:** At 20 traces, models perform well (95%+). At 100+ traces, models start missing connections. At 500+ traces, models significantly underperform the tool.

**What this proves:**
- The tool's reason to exist: human-level semantic understanding + machine-level completeness tracking
- Which models are better/worse at raw traceability (interesting data)
- The exact threshold where tool-assisted beats model-alone

**Benchmark different models:** Claude Opus, Sonnet, Haiku, GPT-4o, etc. This becomes a published comparison showing where each model breaks down.

### 3. Stress tests

- Compound sentences (traces that must be split to be found)
- Implicit traces (word choice implications)
- Override scenarios (later document contradicts earlier)
- Partial coverage (target addresses topic but misses specific detail)
- Near-miss distractors (target mentions the topic but doesn't actually cover the trace)

## Use Cases

### Primary: Specification verification

An agent writes a specification (system design, functional spec) based on input requirements. tracecart verifies that the written spec covers everything from the input.

**Workflow:**
```
1. Agent receives input requirements (meetings, emails, client docs)
2. Agent writes specification
3. tracecart runs: input requirements (source) vs. written spec (target)
4. tracecart reports: "12 traces MISSING, 8 PARTIAL"
5. Agent receives feedback, iterates on the spec
6. Loop until coverage = 100%
```

This can be called **during** specification writing as a live feedback loop — the agent invokes tracecart after each section to check completeness.

### Secondary use cases

| Use case | Source | Target | Question |
|----------|--------|--------|----------|
| Contract audit | Amendment history | Final contract | Does the contract reflect all amendments? |
| Compliance check | Regulatory requirements | Internal policies | Does our policy cover all regulations? |
| Decision tracking | Meeting notes over time | Decision log | Are all decisions documented? |
| Code review | Spec/design doc | Implementation | Does the code implement everything specified? |
| Translation QA | Original document | Translation | Does the translation cover all points? |
| Handover audit | Project documentation | Handover document | Is the handover complete? |

### Integration pattern: Agent-as-user

tracecart is designed to be called by other agents, not just humans:
- A spec-writing agent calls tracecart as a verification step
- A code-generation agent uses it to verify feature completeness
- A documentation agent uses it to ensure no gaps in docs

## Open Source

The entire project will be open source. Goals:
- Useful to any team dealing with document traceability
- Publishable benchmark results (model comparison)
- Reproducible methodology (Method G + recursive remainder)
- Extensible: new prompts for different languages, new LSP features, new output formats

## Open Questions

- [ ] Should the LSP server hot-reload when trace-map.json changes? (probably yes)
- [ ] How to handle traces that span multiple lines? (range vs single line)
- [ ] Should topic clustering use embeddings (needs SDK) or LLM subagent?
- [ ] How to handle target documents that are not markdown? (PDF, DOCX)
- [ ] Benchmark generator: which domain to use for generated traces? (generic/multi-domain)
- [ ] License choice: MIT vs Apache 2.0?
