## ADDED Requirements

### Requirement: --preset flag on all subcommands
All CLI subcommands that use trace types, coverage statuses, or prompt templates SHALL accept a `--preset <name>` flag.

#### Scenario: split with preset
- **WHEN** user runs `tracecart split source.md --preset spec-coverage`
- **THEN** the command runs using the spec-coverage preset configuration

#### Scenario: extract-prompt with preset
- **WHEN** user runs `tracecart extract-prompt clauses.json --preset spec-coverage`
- **THEN** the extraction prompt is generated using the preset's prompt template and trace types

#### Scenario: match-prompt with preset
- **WHEN** user runs `tracecart match-prompt traces.json target.md --preset spec-coverage`
- **THEN** the matching prompt uses the preset's coverage statuses and prompt template

### Requirement: Command markdown passes --preset
The command markdown recipe SHALL pass `--preset` to every CLI call, using the preset specified in the `/tracecart` invocation or defaulting to `spec-coverage`.

#### Scenario: Default invocation
- **WHEN** user runs `/tracecart source.md target.md`
- **THEN** the recipe runs all CLI commands with `--preset spec-coverage`

#### Scenario: Custom preset invocation
- **WHEN** user runs `/tracecart source.md target.md --preset test-coverage`
- **THEN** the recipe runs all CLI commands with `--preset test-coverage`

### Requirement: Help in command markdown
The command markdown SHALL include a help section that explains available presets, how to create custom ones, and the pipeline steps.

#### Scenario: User asks about presets
- **WHEN** user reads the command markdown or runs `/tracecart --help`
- **THEN** they see a list of built-in presets and instructions for creating custom ones

### Requirement: List presets command
The CLI SHALL support `tracecart presets` to list all available presets (built-in + project-local).

#### Scenario: List presets
- **WHEN** user runs `tracecart presets`
- **THEN** output lists each preset name and description, marking project-local overrides

### Requirement: Archive cleanup
Stale archive files that are superseded by the npm package SHALL be removed.

#### Scenario: Remove stale files
- **WHEN** the change is applied
- **THEN** `archive/annotate_markdown.py`, `archive/format_output.py`, and `archive/examples/` are removed; `archive/python-src/` and `archive/benchmark/` are kept
