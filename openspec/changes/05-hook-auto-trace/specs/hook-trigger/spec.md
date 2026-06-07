## ADDED Requirements

### Requirement: Hook registration
The system SHALL register a Claude Code hook at the `Stop` event that runs the trace verification pipeline.

#### Scenario: Hook configured in settings
- **WHEN** a project has `.set-trace/config.json` with at least one mapping
- **THEN** the hook is registered in `.claude/settings.json` under `hooks.Stop` and runs the trace check script

### Requirement: Change detection via git diff
The hook SHALL determine which files changed since the last clean state using `git diff --name-only` (unstaged and staged) and compare against registered source↔target mappings.

#### Scenario: Target file changed
- **WHEN** `git diff --name-only` includes `specs/order-intake.md` and a mapping has `specs/order-intake.md` as a target
- **THEN** the hook triggers the trace pipeline for that mapping

#### Scenario: Source file changed
- **WHEN** `git diff --name-only` includes `meetings/2024-03-15.md` and a mapping has `meetings/*.md` as a source pattern
- **THEN** the hook triggers the trace pipeline for that mapping

#### Scenario: No relevant files changed
- **WHEN** `git diff --name-only` returns files that do not match any mapping's source or target patterns
- **THEN** the hook exits silently with code 0 and produces no output

### Requirement: Content-hash caching
The hook SHALL cache a hash of source+target file contents after each pipeline run. If file contents match the cached hash, the pipeline SHALL be skipped.

#### Scenario: Files unchanged since last run
- **WHEN** git diff shows changes but the content hash of all mapped files matches the cached hash from the previous run
- **THEN** the hook skips the pipeline and produces no output

#### Scenario: Cache miss
- **WHEN** the content hash does not match (or no cache exists)
- **THEN** the hook runs the pipeline and updates the cache

### Requirement: Silent when not applicable
The hook SHALL produce no output and exit with code 0 when no trace run is needed. The user and LLM SHALL NOT be aware the hook ran.

#### Scenario: No config file
- **WHEN** the project has no `.set-trace/config.json`
- **THEN** the hook exits silently

#### Scenario: No changes detected
- **WHEN** no mapped files changed
- **THEN** the hook exits silently
