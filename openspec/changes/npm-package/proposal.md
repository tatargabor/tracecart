## Why

tracecart is currently a local Python CLI orchestrated manually by Claude Code. To make it usable in other projects, it needs to be an installable npm package with a Claude Code command that automates the full pipeline. Rewriting the ~2100 lines of pure-stdlib Python into TypeScript eliminates the Python runtime dependency — anyone with Node.js (guaranteed by npm) can use it immediately on Mac and Linux.

## What Changes

- **Port Python pipeline to TypeScript**: clause_split, extract, remainder, coverage, trace_map, parse_document, discover_inputs, delta, run_trace — all rewritten in TS with identical logic and JSON I/O contracts
- **npm package structure**: `bin/tracecart` CLI entry point, `src/` TypeScript source, `templates/` for Claude Code command markdown
- **`tracecart init` command**: copies `.claude/commands/set/trace.md` (the orchestration recipe) into the target project
- **`tracecart update` command**: refreshes the command markdown when the package is updated (rare — pipeline structure seldom changes)
- **Claude Code command markdown** (`.claude/commands/set/trace.md`): deterministic recipe that Claude follows step-by-step — runs CLI for deterministic steps, uses Agent tool subagents for LLM steps (extraction, matching), validates LLM output through CLI
- **Test suite port**: existing Python test fixtures and assertions → vitest
- **Python source preserved** in `archive/` for reference

## Capabilities

### New Capabilities
- `cli-package`: npm package structure, bin entry point, `tracecart init`, `tracecart update`, version management
- `ts-pipeline`: TypeScript port of the deterministic pipeline (split, extract-validate, remainder, match-validate, finalize, delta, status)
- `claude-command`: the command markdown recipe that orchestrates deterministic CLI + LLM subagent steps from Claude Code

### Modified Capabilities

## Impact

- **New files**: `package.json`, `tsconfig.json`, `bin/tracecart.ts`, `src/` (TS), `templates/claude/commands/set/trace.md`
- **Preserved**: `lsp/` (Python, stays as-is — separate concern), `prompts/`, `benchmark/`, `tests/fixtures/`
- **Archived**: `src/` Python files move to `archive/python-src/`
- **Dependencies**: zero runtime deps (pure Node.js stdlib). Dev deps: typescript, vitest
- **Platforms**: Mac + Linux (Node.js ≥ 18). Claude Code desktop, CLI, and cowork (claude.ai/code)
