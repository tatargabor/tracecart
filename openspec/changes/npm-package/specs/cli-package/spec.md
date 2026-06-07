## ADDED Requirements

### Requirement: Global CLI installation
The package SHALL be installable via `npm install -g @tracecart/cli` and provide a `tracecart` binary on PATH.

#### Scenario: Fresh install
- **WHEN** user runs `npm install -g @tracecart/cli`
- **THEN** `tracecart --version` prints the package version and exits 0

#### Scenario: Subcommand dispatch
- **WHEN** user runs `tracecart <subcommand> [args]`
- **THEN** the CLI dispatches to the corresponding pipeline function with parsed arguments

### Requirement: Subcommand interface matches Python CLI
The CLI SHALL support the same subcommands as `python3 src/run_trace.py`: `split`, `extract-prompt`, `extract-validate`, `remainder`, `match-prompt`, `match-validate`, `reverse-extract-validate`, `reverse-match-prompt`, `reverse-match-validate`, `finalize`, `status`, `delta`.

#### Scenario: split subcommand
- **WHEN** user runs `tracecart split <source.md> [--lang hu|en]`
- **THEN** output is JSON with `source_file`, `total_lines`, `content_clauses`, `compound_lines_split`, `clauses` fields, identical to the Python output

#### Scenario: Unknown subcommand
- **WHEN** user runs `tracecart nonexistent`
- **THEN** CLI prints usage help to stderr and exits with code 1

### Requirement: init command
`tracecart init` SHALL copy the command markdown template into the target project's `.claude/commands/set/trace.md`.

#### Scenario: Init in project without existing command
- **WHEN** user runs `tracecart init` in a project directory
- **THEN** `.claude/commands/set/trace.md` is created with the recipe from the installed package, and the CLI prints confirmation

#### Scenario: Init with existing command (older version)
- **WHEN** `.claude/commands/set/trace.md` already exists with an older version comment
- **THEN** CLI asks for confirmation before overwriting

#### Scenario: Init with existing command (same version)
- **WHEN** `.claude/commands/set/trace.md` already exists with the same version
- **THEN** CLI prints "Already up to date" and exits

### Requirement: update command
`tracecart update` SHALL refresh the command markdown if the installed package version is newer.

#### Scenario: Newer version available
- **WHEN** user runs `tracecart update` and the package version is newer than the project's command markdown version
- **THEN** the command markdown is replaced with the new version

#### Scenario: Already current
- **WHEN** user runs `tracecart update` and versions match
- **THEN** CLI prints "Already up to date"

### Requirement: Zero runtime dependencies
The package SHALL have zero `dependencies` in package.json. Only `devDependencies` (typescript, vitest) are allowed.

#### Scenario: Package install
- **WHEN** user runs `npm install -g @tracecart/cli`
- **THEN** no transitive runtime dependencies are installed

### Requirement: Prompt template resolution
The CLI SHALL resolve prompt templates from the `prompts/` directory within the installed package, not from the current working directory.

#### Scenario: Run from any directory
- **WHEN** user runs `tracecart extract-prompt clauses.json --lang hu` from any working directory
- **THEN** the CLI finds and uses `prompts/extract_hu.txt` from the package installation path
