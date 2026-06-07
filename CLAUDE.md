# set-trace — Claim Traceability Tool

## What this is

Extract atomic traces from time-ordered source documents, resolve temporal overrides, verify complete coverage against target documents. Visualize via LSP in any editor (primarily Zed).

See DESIGN.md for full architecture and rationale.

## Architecture (summary)

Two layers:
- **Control layer** (deterministic Python): set operations, remainder tracking, termination
- **Semantic layer** (LLM via Claude Code subagents): extraction, entailment, override detection

Output: `trace-map.json` → consumed by LSP server for editor visualization.

## Project structure

```
src/parse/          — deterministic text preprocessing
src/extract/        — trace extraction + recursive remainder
src/match/          — trace-target coverage matching
src/output/         — trace-map.json generation
src/cluster/        — topic grouping (TODO)
src/override/       — temporal override detection (TODO)
lsp/                — LSP server (pygls) for editor integration
prompts/            — LLM prompt templates (hu + en)
benchmark/          — ground truth data (hu + en)
archive/            — old code kept for reference (old benchmark, examples, formatters)
openspec/           — change specifications and artifacts
3rdparty/           — reference implementations (git-ignored)
```

## Running

```bash
# Test clause splitter
echo "text here" | python3 src/parse/clause_split.py - --stats

# Test remainder tracker
python3 src/extract/remainder.py clauses.json traces.json

# LSP server (requires: pip install pygls)
python3 lsp/server.py
```

## Running the pipeline (agent workflow)

The pipeline is orchestrated by a Claude Code agent. Each step is a subcommand of `src/run_trace.py`:

```bash
# Step 1: Split source into clauses
python3 src/run_trace.py split source.md > clauses.json

# Step 2: Generate extraction prompt (send to subagent)
python3 src/run_trace.py extract-prompt clauses.json --source source.md --lang hu

# Step 3: Validate subagent extraction output
python3 src/run_trace.py extract-validate llm_output.txt clauses.json --source source.md > traces.json

# Step 4: Check remainder (loop until complete or not shrinking, max 3 iterations)
python3 src/run_trace.py remainder clauses.json traces.json

# Step 5: Generate coverage matching prompt (send to subagent)
python3 src/run_trace.py match-prompt traces.json target.md --lang hu

# Step 6: Validate subagent matching output
python3 src/run_trace.py match-validate llm_output.txt traces.json > matches.json

# Step 7: Generate trace-map.json
python3 src/run_trace.py finalize traces.json matches.json --source source.md --target target.md --output trace-map.json

# Check pipeline status
python3 src/run_trace.py status traces.json clauses.json
```

The agent interleaves deterministic steps (split, remainder, finalize) with LLM subagent calls (extraction, matching). Test fixtures are in `tests/fixtures/`.

## Development conventions

- Python 3.11+, no external dependencies except pygls for LSP
- LLM calls go through Claude Code subagents (not Anthropic SDK)
- All deterministic code: stdin/stdout JSON, testable offline
- Primary editor target: Zed (then VS Code)
- Prompt templates in `prompts/` — plain text, {variable} placeholders
- Benchmark ground truth is manually verified — don't auto-generate

## Key terminology

| Term | Meaning |
|------|---------|
| **trace** | Atomic assertion from source. Types: REQUIREMENT, DECISION, WISH, OPEN_QUESTION, EXCLUSION |
| **source** | Authoritative input corpus (time-ordered, overrides possible) |
| **target** | Document(s) verified for completeness |
| **coverage** | Whether target addresses a trace: COVERED / PARTIAL / MISSING / DEFERRED / N/A |
| **remainder** | Clauses not yet consumed by any trace (deterministic completeness check) |
| **trace-map** | Universal JSON output format (trace-map.json) |

## Pipeline phases

```
Phase 0: PARSE (det)     — clause_split + parse_document + discover_inputs
Phase 1: EXTRACT (LLM)   — recursive remainder extraction
Phase 2: CLUSTER (det)    — topic grouping for scale
Phase 3: OVERRIDE (LLM)  — temporal supersession detection
Phase 4: MATCH (LLM)     — trace → target coverage check
Phase 5: OUTPUT (det)     — trace-map.json generation
```

## 3rd party references (in 3rdparty/, git-ignored)

| Tool | Learning |
|------|----------|
| Claimify | Claim extraction pipeline design |
| MiniCheck | Entailment checking approach |
| FActScore | Atomic decomposition + scoring |
| OpenFactVerification | Multi-step pipeline |
| Doorstop | Traceability data structures |
| Factcheck-GPT | End-to-end pipeline |
