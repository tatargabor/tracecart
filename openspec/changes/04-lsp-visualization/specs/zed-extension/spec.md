## ADDED Requirements

### Requirement: Zed extension manifest
The project SHALL include a Zed extension configuration that registers the tracecart LSP server for markdown files.

#### Scenario: Extension activates on markdown
- **WHEN** a user opens a .md file in a workspace containing trace-map.json
- **THEN** Zed activates the tracecart LSP server

#### Scenario: Extension does not activate without trace-map
- **WHEN** a user opens a .md file in a workspace WITHOUT trace-map.json
- **THEN** the tracecart LSP server is NOT activated

### Requirement: Zero-config installation
The Zed extension SHALL work with minimal setup: install the extension, have pygls installed, and trace-map.json in the project root.

#### Scenario: First-time setup
- **WHEN** a user installs the Zed extension and has `pip install pygls` done
- **THEN** opening a project with trace-map.json immediately shows coverage diagnostics

### Requirement: Extension documentation
The extension SHALL include a brief README explaining: what it does, how to install, prerequisites (pygls), and how to generate trace-map.json.

#### Scenario: User reads README
- **WHEN** a user finds the extension
- **THEN** they can go from zero to working diagnostics in under 5 minutes
