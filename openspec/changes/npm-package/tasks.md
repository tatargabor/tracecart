## 1. Project scaffold

- [x] 1.1 Create `package.json` with name, version, bin field, zero runtime deps, vitest + typescript as devDeps
- [x] 1.2 Create `tsconfig.json` targeting ES2022, Node18 module resolution, strict mode
- [x] 1.3 Create `src/cli.ts` entry point with subcommand dispatch (split, extract-prompt, extract-validate, remainder, match-prompt, match-validate, reverse-extract-validate, reverse-match-prompt, reverse-match-validate, finalize, status, delta, init, update)
- [x] 1.4 Add build script (`tsc`) and verify `dist/cli.js` runs as `set-trace --version`

## 2. Port parse modules

- [x] 2.1 Port `clause_split.py` → `src/parse/clause-split.ts` (regex splitting, header detection, compound line handling)
- [x] 2.2 Port `parse_document.py` → `src/parse/parse-document.ts` (chapter detection, content block extraction)
- [x] 2.3 Port `discover_inputs.py` → `src/parse/discover-inputs.ts` (file classification, date extraction from filenames)
- [x] 2.4 Test: fixture test1 + test2 clause split output matches Python reference

## 3. Port extract modules

- [x] 3.1 Port `extract.py` → `src/extract/extract.ts` (format_prompt, validate_traces, merge_traces, file hash for trace IDs)
- [x] 3.2 Port `remainder.py` → `src/extract/remainder.ts` (compute_remainder, is_complete, extraction_stats)
- [x] 3.3 Test: extraction validation against fixture data, remainder computation matches Python

## 4. Port match module

- [x] 4.1 Port `coverage.py` → `src/match/coverage.ts` (format_prompt, validate_matches, apply_matches, format_reverse_prompt, validate_reverse_matches, apply_reverse_matches, resolve_refs)
- [x] 4.2 Test: match validation against fixture data

## 5. Port output modules

- [x] 5.1 Port `trace_map.py` → `src/output/trace-map.ts` (build_trace_map, compute_summary)
- [x] 5.2 Port `delta.py` → `src/output/delta.ts` (compare, format_text)
- [x] 5.3 Test: trace-map generation and delta comparison against fixture data

## 6. Port run_trace subcommands

- [x] 6.1 Wire `cmd_split` in cli.ts — calls clause-split, outputs JSON to stdout
- [x] 6.2 Wire `cmd_extract_prompt` — reads clauses JSON, loads prompt template from package's `prompts/`, outputs formatted prompt
- [x] 6.3 Wire `cmd_extract_validate` — reads LLM output + clauses, outputs validated traces JSON
- [x] 6.4 Wire `cmd_remainder` — reads clauses + traces, outputs remainder stats JSON
- [x] 6.5 Wire `cmd_match_prompt` — reads traces + target, loads prompt template, outputs formatted prompt
- [x] 6.6 Wire `cmd_match_validate` — reads LLM output + traces, outputs validated matches JSON
- [x] 6.7 Wire reverse trace subcommands (reverse-extract-validate, reverse-match-prompt, reverse-match-validate)
- [x] 6.8 Wire `cmd_finalize` — reads traces + matches, outputs trace-map.json
- [x] 6.9 Wire `cmd_status` and `cmd_delta` subcommands

## 7. Init and update commands

- [x] 7.1 Implement `set-trace init` — copies `templates/claude/commands/set/trace.md` to project `.claude/commands/set/trace.md`, creates directories if needed
- [x] 7.2 Implement `set-trace update` — reads version comment from project command markdown, compares with package version, replaces if newer
- [x] 7.3 Test: init creates file, update detects staleness, same-version skips

## 8. Command markdown (the recipe)

- [x] 8.1 Write `templates/claude/commands/set/trace.md` — deterministic step-by-step recipe for Claude Code: parse args → split → extract loop (subagent + validate + remainder, max 3) → match (subagent + validate) → finalize → report
- [x] 8.2 Include version comment (`<!-- set-trace v0.1.0 -->`) in the template
- [ ] 8.3 Test: manually run `/set:trace` against test fixtures, verify trace-map.json output

## 9. Archive and cleanup

- [x] 9.1 Move Python `src/` to `archive/python-src/` for reference
- [x] 9.2 Copy test fixtures to `tests/fixtures/` (keep existing structure)
- [x] 9.3 Update CLAUDE.md with new running instructions (`set-trace` instead of `python3 src/run_trace.py`)
- [x] 9.4 Update `.gitignore` for `dist/`, `node_modules/`
