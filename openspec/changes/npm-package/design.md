## Context

set-trace is a traceability pipeline that extracts atomic traces from source documents and verifies coverage against target documents. The core engine is ~2100 lines of pure-stdlib Python (no external dependencies), orchestrated manually by Claude Code. The pipeline alternates deterministic steps (split, validate, remainder, finalize) with LLM steps (extraction, matching) handled by Claude Code subagents.

The goal is to package this as an npm package so anyone can `npm install -g`, run `set-trace init` in their project, and use `/set:trace` from Claude Code to run the full pipeline.

## Goals / Non-Goals

**Goals:**
- npm package installable globally, works on Mac + Linux with Node.js ≥ 18
- `set-trace <subcommand>` CLI with identical behavior to current `python3 src/run_trace.py <subcommand>`
- `set-trace init` copies Claude Code command markdown into target project
- Zero runtime dependencies (pure Node.js stdlib: fs, path, crypto, child_process not needed)
- All existing test fixtures produce identical output after port
- Command markdown is a deterministic recipe Claude Code follows without interpretation

**Non-Goals:**
- LSP server port (stays Python/pygls, separate concern)
- Windows support (v1: Mac + Linux only)
- Prompt template changes (reuse existing `prompts/` as-is)
- New pipeline features (override phase, clustering — future work)
- Python code removal (archived, not deleted)

## Decisions

### 1. TypeScript over Python for distribution

Port all pipeline code to TypeScript. The code is pure text processing (regex, JSON, sets) with zero Python-specific constructs.

**Why not keep Python + uv:** Every user would need Python 3.11+ or uv installed. npm users have Node.js guaranteed. One less runtime = zero friction install.

**Why not compile Python to binary (PyInstaller):** Platform-specific binaries (~50MB each), complex cross-compilation, maintenance burden.

### 2. 1:1 function-level port, not a rewrite

Each Python module maps to a TypeScript module with the same exports and JSON I/O contracts. No refactoring, no new abstractions. The Python tests define the contract — port passes when output matches.

**Why:** Minimizes risk. The Python code is tested and working. A rewrite would introduce new bugs. The port is mechanical.

### 3. Orchestration recipe in command markdown, not in code

The pipeline step sequence lives in `.claude/commands/set/trace.md` — a markdown file that Claude Code reads and follows deterministically. The CLI provides stateless subcommands; the command markdown defines the order, loops, and subagent calls.

**Why not a Python/TS orchestrator:** The command markdown is readable, auditable, and deterministic. Claude follows explicit steps instead of interpreting a protocol. The pipeline structure rarely changes; when it does, `set-trace update` refreshes the markdown.

**Why not fully automatic (CLI runs everything):** The LLM steps (extraction, matching) must go through Claude Code subagents. There's no way for a CLI to invoke Claude Code's Agent tool. The command markdown is the natural bridge.

### 4. `set-trace init` copies, `set-trace update` refreshes

`init` copies the command markdown template from the installed package into the project's `.claude/commands/set/`. `update` compares versions and replaces if newer.

**Why copy, not symlink:** Symlinks break across environments. Copied files are self-contained and work in any CI/editor. The markdown includes a version comment for staleness detection.

### 5. Package structure

```
package.json          ← bin: { "set-trace": "./dist/cli.js" }
tsconfig.json
src/
  cli.ts              ← entry point, subcommand dispatch
  parse/
    clause-split.ts   ← from clause_split.py
    parse-document.ts ← from parse_document.py
    discover-inputs.ts← from discover_inputs.py
  extract/
    extract.ts        ← from extract.py
    remainder.ts      ← from remainder.py
  match/
    coverage.ts       ← from coverage.py
  output/
    trace-map.ts      ← from trace_map.py
    delta.ts          ← from delta.py
templates/
  claude/
    commands/
      set/
        trace.md      ← the recipe
prompts/              ← unchanged, plain text templates
tests/
  fixtures/           ← from tests/fixtures/ (unchanged)
  *.test.ts           ← vitest tests
```

### 6. Prompt templates stay as plain text files

The `prompts/` directory contains `{variable}` placeholder templates. These are read at runtime and interpolated. No change to format or content.

**Why not embed in TS:** Prompts are the most frequently tuned part. Plain text files are editable without rebuilding.

## Risks / Trade-offs

- **[Port correctness]** TypeScript regex behavior differs subtly from Python (Unicode handling, named groups). → Mitigation: test every module against fixture data, diff outputs byte-for-byte.
- **[Node.js version]** Requiring Node.js ≥ 18 excludes older systems. → Mitigation: 18 is LTS, mainstream. ≥ 20 if we need newer APIs.
- **[Command markdown staleness]** After `set-trace init`, the copied markdown can go stale. → Mitigation: version comment in markdown + `set-trace update` command. Pipeline structure changes are rare (annually).
- **[Prompt path resolution]** The CLI must find `prompts/` relative to the installed package, not cwd. → Mitigation: `__dirname`-relative path resolution in cli.ts.
