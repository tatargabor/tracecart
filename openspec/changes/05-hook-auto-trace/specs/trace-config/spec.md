## ADDED Requirements

### Requirement: Configuration file format
The system SHALL read source↔target file mappings from `.tracecart/config.json` in the project root.

#### Scenario: Valid config with one mapping
- **WHEN** `.tracecart/config.json` contains `{"mappings": [{"name": "order-intake", "sources": ["meetings/*.md"], "targets": ["specs/order-intake.md"]}]}`
- **THEN** the system recognizes one mapping named "order-intake" with the specified source and target patterns

#### Scenario: Multiple mappings
- **WHEN** config contains two mappings with different names, sources, and targets
- **THEN** each mapping is evaluated independently for change detection and pipeline runs

#### Scenario: Glob pattern matching
- **WHEN** a source pattern is `meetings/*.md` and the changed file is `meetings/2024-03-15.md`
- **THEN** the file matches the pattern

### Requirement: Config validation
The system SHALL validate the config file on load and report clear errors for malformed configuration.

#### Scenario: Missing required field
- **WHEN** a mapping lacks the `sources` field
- **THEN** the system prints an error identifying the mapping and the missing field, and skips that mapping

#### Scenario: Config file not found
- **WHEN** `.tracecart/config.json` does not exist
- **THEN** the system exits silently (no error — the project simply doesn't use tracecart)

### Requirement: Mapping name uniqueness
Each mapping SHALL have a unique `name` field used for output directory naming and human-readable reporting.

#### Scenario: Duplicate mapping names
- **WHEN** two mappings share the same `name`
- **THEN** the system reports an error and refuses to run
