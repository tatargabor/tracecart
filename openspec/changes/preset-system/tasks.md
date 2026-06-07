## 1. Preset loader

- [ ] 1.1 Create `src/preset.ts` — loadPreset(name, pkgRoot), resolvePreset (project-local then built-in), validatePreset (check required fields), listPresets
- [ ] 1.2 Define `Preset` interface: name, description?, version?, trace_types, coverage_statuses, prompts (record of role→filename), defaults?
- [ ] 1.3 Test: load built-in preset, load project-local override, missing preset error, invalid preset error

## 2. Default preset file

- [ ] 2.1 Create `presets/spec-coverage.json` — extract current hardcoded values: trace types, coverage statuses, prompt filenames
- [ ] 2.2 Verify: loading this preset + running the pipeline produces identical output to current hardcoded behavior

## 3. Consolidate prompts to English

- [ ] 3.1 Replace `prompts/extract.txt` (Hungarian) with English version from `prompts/en/extract.txt`
- [ ] 3.2 Replace `prompts/coverage_check.txt` with English version from `prompts/en/coverage_check.txt`
- [ ] 3.3 Replace `prompts/reverse_check.txt` with English version from `prompts/en/reverse_check.txt`
- [ ] 3.4 Remove `prompts/en/` directory (no longer needed, English is now the default)
- [ ] 3.5 Add `{trace_types}` and `{coverage_statuses}` placeholders to prompt templates, replacing hardcoded lists

## 4. Wire preset into CLI

- [ ] 4.1 Add `--preset` flag parsing to `src/cli.ts` — parse before subcommand dispatch, pass loaded preset to command functions
- [ ] 4.2 Update `src/commands/extract-prompt.ts` — use preset for prompt template resolution and trace types
- [ ] 4.3 Update `src/commands/match-prompt.ts` — use preset for prompt template resolution and coverage statuses
- [ ] 4.4 Update `src/commands/reverse-match-prompt.ts` — use preset for prompt template resolution
- [ ] 4.5 Update `src/commands/extract-validate.ts` — validate trace types against preset
- [ ] 4.6 Update `src/commands/match-validate.ts` — validate coverage statuses against preset
- [ ] 4.7 Add `set-trace presets` subcommand — lists available presets with descriptions

## 5. Update command markdown

- [ ] 5.1 Update `templates/claude/commands/set/trace.md` — add `--preset` to all CLI calls, parse preset from arguments
- [ ] 5.2 Add help section to command markdown — explain presets, list built-ins, how to create custom
- [ ] 5.3 Bump version comment to `<!-- set-trace v0.2.0 -->`
- [ ] 5.4 Run `set-trace update` to refresh the project's command markdown

## 6. Archive cleanup

- [ ] 6.1 Remove `archive/annotate_markdown.py`, `archive/format_output.py`, `archive/examples/`
- [ ] 6.2 Keep `archive/python-src/` and `archive/benchmark/`
- [ ] 6.3 Remove `prompts/verify.txt` if unused by any preset

## 7. End-to-end test

- [ ] 7.1 Run `/set:trace tests/fixtures/test1/source.md tests/fixtures/test1/target.md` with spec-coverage preset — verify same results as before
- [ ] 7.2 Verify `set-trace presets` lists spec-coverage with description
