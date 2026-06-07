## Context

tracecart has a forward trace pipeline (source→target) defined in 01-core-engine: extract traces from source documents, match against target sections, report coverage. The extraction pipeline (clause_split → LLM extract → remainder loop) and matching pipeline (trace × target section → status) are designed but not yet fully implemented.

The reverse direction (target→source) was deferred to "v2" in 01-core-engine, but the hook-based automatic verification use case requires it immediately. When an LLM modifies a target document, we need to know both:
- What source claims are MISSING from the target (forward)
- What target claims have NO source backing (reverse)

Existing code that this change builds on:
- `src/parse/clause_split.py` — works on any text, not source-specific
- `src/extract/remainder.py` — works on any clauses+traces, direction-agnostic
- `src/output/trace_map.py` — needs extension for reverse traces
- `prompts/extract.txt` — extraction prompt, reusable for target extraction
- `prompts/coverage_check.txt` — matching prompt, needs role-swap variant

## Goals / Non-Goals

**Goals:**
- Extract atomic claims from target documents using the same extraction pipeline as source
- Match target claims against source traces to determine traceability
- Report `UNTRACED_IN_SOURCE` for target claims with no source backing
- Extend trace-map.json with reverse trace data
- Keep the reverse pipeline zero-new-code where possible (reuse extraction + matching)

**Non-Goals:**
- Classifying WHY something is untraced (hallucination vs. creative addition vs. external source) — the user decides
- Automated correction of untraced claims — tracecart reports, doesn't fix
- Reverse trace for temporal override detection — that's still v2
- Performance optimization for large target documents — v1 targets 50 traces scale

## Decisions

### 1. Reuse extraction pipeline on target documents, don't write new code

The same `clause_split.py → LLM extract → remainder loop` runs on target documents. The extraction prompt (`extract.txt`) works on any text — it finds atomic assertions regardless of whether the text is "source" or "target."

**Rationale:** The extraction problem is symmetric. A claim is a claim whether it appears in meeting notes or a design doc. Reusing the pipeline means zero new extraction code and identical quality guarantees (remainder tracking, entity check).

**Alternative considered:** Lightweight target parsing (just split by section, treat each section as one claim). Rejected: misses compound sentences, implicit claims, and gives coarser granularity than source traces — making matching unreliable.

### 2. Reverse matching: same entailment check, swapped roles

Forward matching asks: "Does target section X cover source trace Y?"
Reverse matching asks: "Does source trace set cover target claim Z?"

The entailment check is the same — `coverage_check.txt` prompt with roles swapped. The target claim becomes the "trace to verify" and the source traces become the "document to check against."

**Rationale:** Entailment is directional but the mechanism is identical. A single prompt template with parameterized roles avoids maintaining two separate matching codepaths.

**Implementation:** Add a `direction` parameter to the matching module. `forward` = source traces vs target sections. `reverse` = target claims vs source traces. The prompt template uses `{claim}` and `{evidence}` placeholders instead of hardcoded "trace" and "target."

### 3. Output: `reverse_traces` as separate section in trace-map.json

```json
{
  "version": 1,
  "traces": [ ... ],           // forward: source→target (existing)
  "reverse_traces": [          // NEW: target→source
    {
      "id": "RT-b2d4e7-012-0",
      "text": "Minden rendelés max 48h-n belül visszaigazolásra kerül",
      "source": {"file": "design.md", "line": 12},
      "status": "UNTRACED_IN_SOURCE",
      "nearest_source_trace": "T-a3f2c1-047-0",  // closest match, if any
      "similarity_note": "source mentions confirmation but no 48h deadline"
    }
  ],
  "summary": {
    // existing forward stats...
    "reverse_total": 45,
    "reverse_traced": 42,
    "reverse_untraced": 3,
    "reverse_coverage_pct": 93.3
  }
}
```

**Rationale:** Separate section keeps backward compatibility — consumers that don't know about `reverse_traces` ignore it. The `nearest_source_trace` field gives context: "this claim is SIMILAR to source trace X but not fully supported" vs. "this claim has no relation to any source."

**Alternative considered:** Merging reverse traces into the main `traces` array with a `direction` field. Rejected: breaks existing consumers and conflates two conceptually different questions (coverage vs. provenance).

### 4. Reverse trace IDs: `RT-` prefix

Forward traces: `T-{hash6}-{line}-{clause}`
Reverse traces: `RT-{hash6}-{line}-{clause}`

**Rationale:** Clear namespace separation. The hash is derived from the target file path (same algorithm as forward). IDs are deterministic and git-diffable.

### 5. "Nearest source trace" as soft link, not hard match

When a target claim is `UNTRACED_IN_SOURCE`, the system attempts to find the closest source trace (by semantic similarity via the LLM). This is advisory — it helps the user understand WHY it's untraced:
- Close match → probably a distortion/exaggeration of a real source claim
- No close match → probably hallucinated or from an unknown source

**Rationale:** A bare "UNTRACED" flag is less actionable than "UNTRACED, but similar to T-a3f2c1-047 which says X." The user can decide faster.

**Implementation:** During reverse matching, if a target claim gets no COVERED match, ask the LLM: "Which source trace is most similar, if any?" This piggybacks on the matching call — one extra field in the response, not an extra LLM call.

## Risks / Trade-offs

**[Risk] Target extraction doubles pipeline runtime** — extracting from both source and target means 2× the LLM calls.
→ Mitigation: At v1 scale (50 traces), this is acceptable. Target documents are typically more structured than source (meeting notes), so extraction may actually be faster. Optimization deferred.

**[Risk] Reverse matching at scale is O(m×n)** — every target claim checked against every source trace.
→ Mitigation: Same scale constraint as forward matching. Topic clustering (v2) will help both directions equally.

**[Risk] "Nearest source trace" may be misleading** — LLM might pick a superficially similar but semantically unrelated trace.
→ Mitigation: The field is advisory and clearly labeled. Include a `similarity_note` explaining why the LLM chose it. The user makes the final call.

**[Risk] Some target claims are legitimately not from source** — boilerplate, structure, cross-references, formatting decisions.
→ Mitigation: The extraction prompt should be tuned to skip meta-content (headings, cross-refs, boilerplate) and focus on substantive claims. Some false positives are acceptable — the user filters.
