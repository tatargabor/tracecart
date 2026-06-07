## Why

The pipeline currently hardcodes a single use case: "meeting notes → functional spec coverage" with Hungarian-specific prompt templates, trace types (REQUIREMENT, DECISION, WISH, EXCLUSION, OPEN_QUESTION), and coverage statuses (COVERED, PARTIAL, MISSING, DEFERRED, N/A). To make tracecart usable for other comparison types (test coverage, contract compliance, changelog consistency) without forking the codebase, the domain-specific configuration needs to be extracted into a preset system.

## What Changes

- **Preset format**: JSON/YAML files that define trace types, coverage statuses, prompt template references, and language — everything domain-specific
- **Default preset**: `spec-coverage` — extracts the current hardcoded configuration into a preset file, zero behavior change
- **CLI integration**: all subcommands accept `--preset <name>`, defaulting to `spec-coverage`
- **Prompt template resolution**: prompts looked up via preset config instead of hardcoded paths
- **Preset discovery**: built-in presets ship with the package, custom presets loadable from project directory
- **English-only prompts**: single prompt language (English), LLM handles source/target in any language. Prompt templates parameterized by preset vocabulary (trace types, statuses)
- **BREAKING**: prompt template path resolution changes (internal, not user-facing)

## Capabilities

### New Capabilities
- `preset-format`: preset file format, schema, loading, validation, and discovery (built-in + project-local)
- `preset-cli`: CLI integration — `--preset` flag on all subcommands, preset-aware prompt template resolution

### Modified Capabilities

## Impact

- **Modified files**: `src/cli.ts` (preset loading), `src/extract/extract.ts` (prompt resolution via preset), `src/match/coverage.ts` (prompt resolution via preset, status vocabulary from preset)
- **New files**: `presets/spec-coverage.json` (default), `src/preset.ts` (loader/validator)
- **Modified**: `prompts/` — consolidated to English-only, parameterized by preset vocabulary
- **Templates**: `templates/claude/commands/set/trace.md` — updated to pass `--preset` flag
