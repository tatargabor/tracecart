<!-- set-trace v0.2.0 -->
---
name: "SET: Trace"
description: "Run the full trace pipeline: source → target → trace-map.json. Deterministic CLI steps + LLM subagent extraction and matching."
---

# Trace Pipeline

Run the complete set-trace pipeline to extract traces from source documents and verify coverage against target documents.

**Input**: `/set:trace <source> <target> [--preset <name>]`

- `<source>`: path to the source document (authoritative input, e.g., meeting notes)
- `<target>`: path to the target document (verified for completeness, e.g., spec)
- `--preset`: preset name, defaults to `spec-coverage`. Run `set-trace presets` to list available presets.

Parse `$ARGUMENTS` to extract these. If arguments are missing, ask the user.

## Presets

Presets define the domain vocabulary (trace types, coverage statuses) and prompt templates used by the pipeline. The same pipeline structure works for different use cases by switching presets.

**Built-in presets:**
- `spec-coverage` — Source requirements → target spec coverage verification (default)

**Custom presets:** Place a JSON file in `./presets/<name>.json` in your project. Project-local presets override built-in ones by name.

**Preset format:**
```json
{
  "name": "my-preset",
  "description": "What this preset checks",
  "version": "1.0",
  "trace_types": ["TYPE_A", "TYPE_B"],
  "coverage_statuses": ["STATUS_A", "STATUS_B"],
  "prompts": {
    "extract": "extract.txt",
    "coverage_check": "coverage_check.txt",
    "reverse_check": "reverse_check.txt"
  }
}
```

## Pipeline Steps

Execute these steps in order. Each step is explicit — follow exactly as written.

### Step 1: Split source into clauses

```bash
set-trace split <source> > /tmp/set-trace-clauses.json
```

Report: "Split complete: N content clauses from M lines."

### Step 2: Extract traces (LLM loop — max 3 iterations)

Set `iteration = 1` and `previous_remaining = Infinity`.

**Loop:**

#### 2a. Generate extraction prompt

```bash
set-trace extract-prompt /tmp/set-trace-clauses.json --source <source> --preset <preset> > /tmp/set-trace-extract-prompt.txt
```

#### 2b. Send to subagent

Use the **Agent tool** to spawn a subagent with the content of `/tmp/set-trace-extract-prompt.txt` as the prompt. The subagent should return a JSON array of extracted traces.

Save the subagent's full response to `/tmp/set-trace-extract-raw.txt`.

#### 2c. Validate extraction

```bash
set-trace extract-validate /tmp/set-trace-extract-raw.txt /tmp/set-trace-clauses.json --source <source> --preset <preset> > /tmp/set-trace-traces.json
```

Report any validation errors from the output.

#### 2d. Check remainder

```bash
set-trace remainder /tmp/set-trace-clauses.json /tmp/set-trace-traces.json > /tmp/set-trace-remainder.json
```

Read the output and check:
- `stats.clauses_remaining`: number of uncovered clauses
- `stats.coverage_pct`: coverage percentage

**Decision:**
- If `clauses_remaining == 0`: extraction complete, go to Step 3
- If `clauses_remaining < previous_remaining` AND `iteration < 3`:
  set `previous_remaining = clauses_remaining`, increment `iteration`, go back to 2a
- Otherwise (stalled or max iterations): report remainder count, go to Step 3

Report: "Extraction iteration N: coverage_pct% (remaining clauses)."

### Step 3: Match traces against target (LLM)

#### 3a. Generate matching prompt

```bash
set-trace match-prompt /tmp/set-trace-traces.json <target> --preset <preset> > /tmp/set-trace-match-prompt.txt
```

#### 3b. Send to subagent

Use the **Agent tool** to spawn a subagent with the content of `/tmp/set-trace-match-prompt.txt` as the prompt. The subagent should return a JSON array of coverage assessments.

Save the subagent's full response to `/tmp/set-trace-match-raw.txt`.

#### 3c. Validate matching

```bash
set-trace match-validate /tmp/set-trace-match-raw.txt /tmp/set-trace-traces.json --preset <preset> > /tmp/set-trace-matches.json
```

Report any validation errors.

### Step 4: Finalize

```bash
set-trace finalize /tmp/set-trace-traces.json /tmp/set-trace-matches.json --source <source> --target <target> --output trace-map.json
```

### Step 5: Report

Read `trace-map.json` and report the coverage summary:
- Total traces
- COVERED / PARTIAL / MISSING / DEFERRED / N/A counts
- Coverage score percentage

If there are MISSING traces, list the top 5 with their text.

## Notes

- All intermediate files go to `/tmp/set-trace-*` to avoid polluting the project directory
- The extraction loop (Step 2) runs max 3 iterations and stops early if remainder doesn't shrink
- Each subagent call is independent — the prompt contains all context the subagent needs
- If any step fails, report the error and stop — don't continue with partial data
