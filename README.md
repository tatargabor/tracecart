# set-trace

Claim traceability tool — extract atomic traces from source documents, verify coverage against targets, detect unsupported claims via reverse tracing.

## Install

```bash
npm install -g @set-trace/cli
```

## Usage

### As a Claude Code skill

```bash
# Install command into your project
set-trace init

# Run the full pipeline (forward)
/set:trace source.md target.md --preset spec-coverage

# Forward + reverse (detect unsupported claims in target)
/set:trace source.md target.md --reverse
```

### CLI commands

```bash
# Split source into clauses
set-trace split source.md

# Generate extraction prompt
set-trace extract-prompt clauses.json --source source.md --preset spec-coverage

# Validate extraction output
set-trace extract-validate llm_output.txt clauses.json --source source.md --preset spec-coverage

# Check remainder (uncovered clauses)
set-trace remainder clauses.json traces.json

# Generate coverage matching prompt
set-trace match-prompt traces.json target.md --preset spec-coverage

# Validate matching output
set-trace match-validate llm_output.txt traces.json --preset spec-coverage

# Finalize trace-map
set-trace finalize traces.json matches.json --source source.md --target target.md --output trace-map.json

# List available presets
set-trace presets
```

## Architecture

Two layers:
- **Control layer** (deterministic TypeScript): clause splitting, validation, remainder tracking, finalization
- **Semantic layer** (LLM via Claude Code subagents): extraction, coverage matching, reverse tracing

```
Source documents
  → Split into clauses (deterministic)
  → Extract traces (LLM, max 3 iterations)
  → Match traces against target (LLM)
  → [optional] Reverse trace: target → source (LLM)
  → Output: trace-map.json
```

## Presets

Presets define domain vocabulary (trace types, coverage statuses) and prompt templates. The default `spec-coverage` preset checks requirements coverage.

Custom presets: place a JSON file in `./presets/<name>.json`.

See [docs/presets.md](docs/presets.md) for details.

## Output

`trace-map.json` — consumed by the LSP server for editor visualization (Zed, VS Code).

## Documentation

Detailed documentation is in [`docs/`](docs/):

- [Presets](docs/presets.md) — preset format, customization, discovery
- [Benchmarks](docs/benchmarks.md) — extraction method comparison and scoring
- [Testing](docs/testing.md) — test fixtures, running tests, adding ground truth

## Development

```bash
npm run build       # Compile TypeScript
npm run dev         # Watch mode
npm test            # Run tests
```

Zero runtime dependencies. Node.js >= 18.

## License

MIT
