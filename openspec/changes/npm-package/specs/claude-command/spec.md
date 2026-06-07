## ADDED Requirements

### Requirement: Command markdown defines deterministic pipeline recipe
The command markdown at `.claude/commands/set/trace.md` SHALL contain explicit step-by-step instructions that Claude Code follows without interpretation.

#### Scenario: Full pipeline execution
- **WHEN** user invokes `/set:trace source.md target.md`
- **THEN** Claude Code executes the steps in order: split → extract (LLM loop) → match (LLM) → finalize, producing `trace-map.json`

#### Scenario: Language flag
- **WHEN** user invokes `/set:trace source.md target.md --lang en`
- **THEN** all pipeline steps use English prompt templates

#### Scenario: Default language
- **WHEN** no `--lang` flag is provided
- **THEN** pipeline defaults to Hungarian (`hu`)

### Requirement: LLM steps use Claude Code subagents
The command markdown SHALL instruct Claude Code to use the Agent tool for LLM steps (extraction and matching), passing the prompt from `set-trace extract-prompt` or `set-trace match-prompt`.

#### Scenario: Extraction subagent
- **WHEN** the recipe reaches the extract step
- **THEN** Claude Code runs `set-trace extract-prompt` to get the prompt, spawns a subagent with that prompt, and saves the subagent's response to a temp file for `set-trace extract-validate`

#### Scenario: Match subagent
- **WHEN** the recipe reaches the match step
- **THEN** Claude Code runs `set-trace match-prompt` to get the prompt, spawns a subagent, and saves the response for `set-trace match-validate`

### Requirement: Remainder loop with bounded iterations
The command markdown SHALL define a remainder loop: after extraction, check remainder; if uncovered clauses decreased, re-extract; max 3 iterations.

#### Scenario: First extraction covers everything
- **WHEN** `set-trace remainder` reports 0 uncovered clauses after first extraction
- **THEN** pipeline proceeds to match step (no loop)

#### Scenario: Remainder shrinks
- **WHEN** `set-trace remainder` reports uncovered clauses but fewer than previous iteration
- **THEN** pipeline runs another extraction round (up to max 3 total)

#### Scenario: Remainder stalls
- **WHEN** uncovered count does not decrease between iterations
- **THEN** pipeline stops the extraction loop and proceeds to match step

#### Scenario: Max iterations reached
- **WHEN** 3 extraction iterations have been completed
- **THEN** pipeline proceeds to match step regardless of remaining uncovered clauses

### Requirement: Pipeline output
The command markdown SHALL instruct Claude Code to report the final result after `set-trace finalize`.

#### Scenario: Successful completion
- **WHEN** pipeline completes successfully
- **THEN** Claude Code reports: path to trace-map.json and the coverage summary (counts per status)

### Requirement: Version tracking in command markdown
The command markdown SHALL include a version comment that `set-trace update` can read.

#### Scenario: Version comment present
- **WHEN** the command markdown is installed via `set-trace init`
- **THEN** the file contains a comment like `<!-- set-trace v0.1.0 -->` that identifies the template version
