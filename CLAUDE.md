# tracecart — Claim Traceability Tool

## What this is

Extract atomic traces from time-ordered source documents, resolve temporal overrides, verify complete coverage against target documents. Visualize via LSP in any editor (primarily Zed).

See DESIGN.md for full architecture and rationale.

## Architecture (summary)

Two layers:
- **Control layer** (deterministic TypeScript): set operations, remainder tracking, termination
- **Semantic layer** (LLM via Claude Code subagents): extraction, entailment, override detection

Output: `trace-map.json` → consumed by LSP server for editor visualization.

## Project structure

```
src/                — TypeScript source (compiled to dist/)
  parse/            — deterministic text preprocessing
  extract/          — trace extraction + recursive remainder
  match/            — trace-target coverage matching
  output/           — trace-map.json generation
  commands/         — CLI command wrappers
  cli.ts            — entry point
templates/          — Claude Code command markdown (installed via tracecart init)
lsp/                — LSP server (pygls) for editor integration
prompts/            — LLM prompt templates (hu + en)
benchmark/          — ground truth data (hu + en)
archive/            — old code kept for reference (Python source, old benchmark, examples)
openspec/           — change specifications and artifacts
3rdparty/           — reference implementations (git-ignored)
```

## Installation

```bash
npm install -g @tracecart/cli
```

## Running

```bash
# Build from source
npm run build

# Test clause splitter
tracecart split source.md

# Run from dist directly (during development)
node dist/cli.js split source.md

# LSP server (requires: pip install pygls)
python3 lsp/server.py
```

## Running the pipeline (agent workflow)

The pipeline can be run via the Claude Code command `/tracecart`:

```bash
# Install command markdown into project
tracecart init

# Then in Claude Code:
/tracecart source.md target.md --lang hu
```

Or manually, each step is a subcommand of `tracecart`:

```bash
# Step 1: Split source into clauses
tracecart split source.md > clauses.json

# Step 2: Generate extraction prompt (send to subagent)
tracecart extract-prompt clauses.json --source source.md --lang hu

# Step 3: Validate subagent extraction output
tracecart extract-validate llm_output.txt clauses.json --source source.md > traces.json

# Step 4: Check remainder (loop until complete or not shrinking, max 3 iterations)
tracecart remainder clauses.json traces.json

# Step 5: Generate coverage matching prompt (send to subagent)
tracecart match-prompt traces.json target.md --lang hu

# Step 6: Validate subagent matching output
tracecart match-validate llm_output.txt traces.json > matches.json

# Step 7: Generate trace-map.json
tracecart finalize traces.json matches.json --source source.md --target target.md --output trace-map.json

# Check pipeline status
tracecart status traces.json clauses.json

# --- Reverse tracing (target→source) ---

# Step R1: Split target into clauses (reuses same split command)
tracecart split target.md > target_clauses.json

# Step R2: Generate extraction prompt for target (reuses extract-prompt)
tracecart extract-prompt target_clauses.json --source target.md --lang hu

# Step R3: Validate target extraction with RT- prefix
tracecart reverse-extract-validate llm_output.txt target_clauses.json --target target.md > reverse_traces.json

# Step R4: Generate reverse matching prompt (target claims vs source traces)
tracecart reverse-match-prompt reverse_traces.json traces.json --lang hu

# Step R5: Validate reverse matching output
tracecart reverse-match-validate llm_output.txt reverse_traces.json > reverse_matches.json

# Step R6: Finalize with both forward and reverse traces
tracecart finalize traces.json matches.json --source source.md --target target.md --reverse-traces applied_reverse.json --output trace-map.json
```

The agent interleaves deterministic steps (split, remainder, finalize) with LLM subagent calls (extraction, matching). Test fixtures are in `tests/fixtures/`.

## Development conventions

- TypeScript (Node.js ≥ 18), zero runtime dependencies
- Python only for LSP server (pygls)
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
