## 1. Preset loader

- [x] 1.1 Create `src/preset.ts` — loadPreset(name, pkgRoot), resolvePreset (project-local then built-in), validatePreset (check required fields), listPresets
- [x] 1.2 Define `Preset` interface: name, description?, version?, trace_types, coverage_statuses, prompts (record of role→filename), defaults?
- [x] 1.3 Test: load built-in preset, load project-local override, missing preset error, invalid preset error

## 2. Default preset file

- [x] 2.1 Create `presets/spec-coverage.json` — extract current hardcoded values: trace types, coverage statuses, prompt filenames
- [x] 2.2 Verify: loading this preset + running the pipeline produces identical output to current hardcoded behavior

## 3. Consolidate prompts to English

- [x] 3.1 Replace `prompts/extract.txt` (Hungarian) with English version from `prompts/en/extract.txt`
- [x] 3.2 Replace `prompts/coverage_check.txt` with English version from `prompts/en/coverage_check.txt`
- [x] 3.3 Replace `prompts/reverse_check.txt` with English version from `prompts/en/reverse_check.txt`
- [x] 3.4 Remove `prompts/en/` directory (no longer needed, English is now the default)
- [x] 3.5 Add `{trace_types}` and `{coverage_statuses}` placeholders to prompt templates, replacing hardcoded lists

## 4. Wire preset into CLI

- [x] 4.1 Add `--preset` flag parsing to `src/cli.ts` — parse before subcommand dispatch, pass loaded preset to command functions
- [x] 4.2 Update `src/commands/extract-prompt.ts` — use preset for prompt template resolution and trace types
- [x] 4.3 Update `src/commands/match-prompt.ts` — use preset for prompt template resolution and coverage statuses
- [x] 4.4 Update `src/commands/reverse-match-prompt.ts` — use preset for prompt template resolution
- [x] 4.5 Update `src/commands/extract-validate.ts` — validate trace types against preset
- [x] 4.6 Update `src/commands/match-validate.ts` — validate coverage statuses against preset
- [x] 4.7 Add `tracecart presets` subcommand — lists available presets with descriptions

## 5. Update command markdown

- [x] 5.1 Update `templates/claude/commands/set/trace.md` — add `--preset` to all CLI calls, parse preset from arguments
- [x] 5.2 Add help section to command markdown — explain presets, list built-ins, how to create custom
- [x] 5.3 Bump version comment to `<!-- tracecart v0.2.0 -->`
- [x] 5.4 Run `tracecart update` to refresh the project's command markdown

## 6. Archive cleanup

- [x] 6.1 Remove `archive/annotate_markdown.py`, `archive/format_output.py`, `archive/examples/`
- [x] 6.2 Keep `archive/python-src/` and `archive/benchmark/`
- [x] 6.3 Remove `prompts/verify.txt` if unused by any preset

## 7. End-to-end test

- [x] 7.1 Run `/tracecart tests/fixtures/test1/source.md tests/fixtures/test1/target.md` with spec-coverage preset — verify same results as before
- [x] 7.2 Verify `tracecart presets` lists spec-coverage with description
