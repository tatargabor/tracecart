## 1. Configuration

- [ ] 1.1 Create config schema and loader: read `.set-trace/config.json`, validate mappings (name uniqueness, required fields), glob pattern parsing
- [ ] 1.2 Create example config for the TerraFurn test fixtures
- [ ] 1.3 Test config validation: missing fields, duplicate names, malformed JSON, missing file

## 2. Change Detection

- [ ] 2.1 Implement git diff change detector: `git diff --name-only` (unstaged + staged), match against mapping glob patterns
- [ ] 2.2 Implement content-hash caching: sha256 of all mapped file contents, store in `.set-trace/cache/{mapping-name}.hash`, skip pipeline on cache hit
- [ ] 2.3 Test change detection: file changed → trigger, file unchanged → skip, file outside mappings → skip, cache hit → skip

## 3. Hook Integration

- [ ] 3.1 Create hook shell script that the Claude Code `Stop` hook calls — runs change detection, then pipeline if needed
- [ ] 3.2 Document hook registration in `.claude/settings.json` (manual setup for now)
- [ ] 3.3 Test hook lifecycle: silent exit when no config, silent exit when no changes, stdout output when findings exist

## 4. Result Feedback

- [ ] 4.1 Implement summary formatter: mapping name + coverage % header, one line per finding (priority: MISSING > UNTRACED > PARTIAL), cap at 10 per mapping
- [ ] 4.2 Implement trace-map.json file output to `.set-trace/output/{mapping-name}/trace-map.json`
- [ ] 4.3 Test output format: verify stdout is human+LLM readable, verify trace-map.json path is included, verify cap at 10 findings

## 5. CLI Entrypoint

- [ ] 5.1 Create `python3 -m set_trace check` CLI — reads config, runs pipeline for all or specific mappings
- [ ] 5.2 Add `--mapping` flag for single mapping, `--source`/`--target` flags for ad-hoc runs
- [ ] 5.3 Implement exit codes: 0 = clean, 1 = findings, 2 = error
- [ ] 5.4 Test CLI: all-mappings run, single-mapping run, ad-hoc run, exit codes

## 6. End-to-End

- [ ] 6.1 End-to-end test: configure hook + modify target file + simulate turn end → verify hook triggers, pipeline runs, stdout contains findings
- [ ] 6.2 Test closed-loop scenario: LLM modifies design.md → hook reports 2 MISSING → verify LLM context contains findings → LLM can read trace-map.json for details
- [ ] 6.3 Document setup in CLAUDE.md: how to configure set-trace hook for a project
