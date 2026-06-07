## ADDED Requirements

### Requirement: Preset JSON schema
A preset file SHALL be a JSON file with the following required fields: `name` (string), `trace_types` (string array), `coverage_statuses` (string array), `prompts` (object mapping prompt roles to filenames).

#### Scenario: Valid preset loaded
- **WHEN** a preset JSON file contains all required fields
- **THEN** the CLI loads it and uses its configuration for all pipeline steps

#### Scenario: Missing required field
- **WHEN** a preset JSON file is missing `trace_types`
- **THEN** the CLI exits with an error naming the missing field

### Requirement: Built-in default preset
The package SHALL ship with a `spec-coverage` preset that reproduces the current hardcoded behavior: trace types REQUIREMENT/DECISION/WISH/OPEN_QUESTION/EXCLUSION, coverage statuses COVERED/PARTIAL/MISSING/DEFERRED/N/A.

#### Scenario: No --preset flag
- **WHEN** user runs `set-trace split source.md` without `--preset`
- **THEN** the CLI uses the `spec-coverage` preset

#### Scenario: Explicit default
- **WHEN** user runs `set-trace split source.md --preset spec-coverage`
- **THEN** behavior is identical to omitting `--preset`

### Requirement: Preset discovery
The CLI SHALL look for presets in order: project-local `./presets/<name>.json`, then package built-in `<pkg>/presets/<name>.json`. First match wins.

#### Scenario: Project-local preset exists
- **WHEN** `./presets/custom.json` exists and user runs `--preset custom`
- **THEN** the CLI loads `./presets/custom.json`

#### Scenario: Built-in preset
- **WHEN** no project-local preset exists and user runs `--preset spec-coverage`
- **THEN** the CLI loads from the package's built-in `presets/spec-coverage.json`

#### Scenario: Preset not found
- **WHEN** user runs `--preset nonexistent` and no file is found
- **THEN** the CLI exits with an error listing available presets

### Requirement: Prompt template resolution via preset
Prompt templates SHALL be resolved from the preset's `prompts` mapping. Template filenames are relative to the package's `prompts/` directory.

#### Scenario: Extract prompt resolution
- **WHEN** preset has `"prompts": {"extract": "extract.txt"}`
- **THEN** `set-trace extract-prompt` loads `<pkg>/prompts/extract.txt`

### Requirement: Prompt templates parameterized by preset vocabulary
Prompt templates SHALL use `{trace_types}` and `{coverage_statuses}` placeholders that are filled from the active preset's configuration.

#### Scenario: Custom trace types in prompt
- **WHEN** a preset defines `trace_types: ["OBLIGATION", "PROHIBITION", "PERMISSION"]`
- **THEN** the extraction prompt lists these types instead of the default REQUIREMENT/DECISION/etc.

### Requirement: English-only prompts
All prompt templates SHALL be in English. The LLM handles source/target documents in any language.

#### Scenario: Hungarian source with English prompt
- **WHEN** source document is in Hungarian and prompts are in English
- **THEN** the LLM correctly extracts traces and matches coverage (confirmed in testing)
