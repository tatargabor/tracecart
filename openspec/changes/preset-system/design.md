## Context

set-trace is an npm package (`@set-trace/cli`) that extracts traces from source documents and verifies coverage against targets. The pipeline is generic (split → extract → match → finalize) but all domain semantics are hardcoded: Hungarian prompt templates, fixed trace types, fixed coverage statuses. The command markdown recipe also hardcodes these assumptions.

From exploration, we confirmed:
- LLM is required for both extraction and matching (deterministic matching fails due to morphology and synonymy)
- English-only prompts work fine even for Hungarian source/target documents — the LLM handles multilingual content
- The pipeline structure doesn't change across use cases, only the vocabulary and prompts

## Goals / Non-Goals

**Goals:**
- Preset file format that captures all domain-specific configuration
- Default `spec-coverage` preset that reproduces current behavior exactly
- CLI accepts `--preset` on all subcommands
- English-only prompt templates, parameterized by preset vocabulary
- Built-in presets ship with the package, custom presets loadable from `./presets/`
- Command markdown updated to pass preset, remains generic
- Help text in the command markdown skill
- Archive cleanup: remove stale files from `archive/` that are no longer useful

**Non-Goals:**
- Deterministic extraction pass (type rules, tag keywords in preset) — deferred, not enough value yet
- Preset marketplace / sharing mechanism
- Multiple prompt languages — English only, LLM handles source language
- GUI for preset creation

## Decisions

### 1. Preset file format: JSON

JSON over YAML because: zero dependencies (Node.js parses JSON natively), consistent with the rest of the pipeline (all I/O is JSON), and simpler to validate.

```json
{
  "name": "spec-coverage",
  "description": "Source requirements → target spec coverage verification",
  "version": "1.0",
  "trace_types": ["REQUIREMENT", "DECISION", "WISH", "OPEN_QUESTION", "EXCLUSION"],
  "coverage_statuses": ["COVERED", "PARTIAL", "MISSING", "DEFERRED", "N/A"],
  "prompts": {
    "extract": "extract.txt",
    "coverage_check": "coverage_check.txt",
    "reverse_check": "reverse_check.txt"
  },
  "defaults": {
    "language": "en"
  }
}
```

Prompt file names are relative to the preset's prompt directory (`prompts/<preset-name>/` or `prompts/` for the default).

### 2. Preset discovery order

1. `./presets/<name>.json` (project-local, highest priority)
2. `<pkg-root>/presets/<name>.json` (built-in)

Project-local presets override built-in ones by name.

### 3. Prompt templates consolidated to English

Currently there are `prompts/` (Hungarian) and `prompts/en/` (English) directories. Consolidate to English-only in `prompts/`. The LLM handles Hungarian/English source text equally well with English prompts (confirmed in testing). Prompt templates use `{trace_types}` and `{coverage_statuses}` placeholders filled from the preset.

### 4. Command markdown gets --preset passthrough

The recipe in `templates/claude/commands/set/trace.md` adds `--preset <preset>` to every CLI call. Default is `spec-coverage`. The recipe also gets a help section explaining available presets and how to create custom ones.

### 5. Archive cleanup

Remove from `archive/`:
- `annotate_markdown.py` — superseded by trace-map + LSP
- `format_output.py` — superseded by trace-map output module
- `examples/` — stale, not referenced
- `benchmark/` — if duplicated in top-level `benchmark/`
- Keep `python-src/` — reference for the TS port

## Risks / Trade-offs

- **[Preset proliferation]** Users might create presets that don't work well. → Mitigation: good defaults, document what makes a preset work.
- **[Prompt template coupling]** Prompts reference trace types/statuses from the preset. If a preset defines types the prompt doesn't mention, LLM may be confused. → Mitigation: the prompt template uses `{trace_types}` placeholder, always in sync.
- **[Breaking change]** Prompt path resolution changes. → Mitigation: internal only, the CLI resolves paths; users never reference prompts directly.
