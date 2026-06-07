# set-trace

[![npm](https://img.shields.io/npm/v/@set-trace/cli)](https://npmjs.com/package/@set-trace/cli)
[![license](https://img.shields.io/npm/l/@set-trace/cli)](LICENSE)

[Documentation](docs/) · [npm](https://www.npmjs.com/package/@set-trace/cli)

**Claim traceability tool** — extract atomic traces from source documents, verify coverage against targets, detect unsupported claims via reverse tracing.

**The problem:** You have input documents (client specs, meeting notes, emails) and generated implementation specs. How do you know the specs cover everything? Manual review misses implicit requirements, compound sentences, and cross-document overrides.

**set-trace** extracts atomic requirements, verifies each against your target documents, and optionally reverse-traces to catch hallucinations. Output: `trace-map.json` for editor visualization.

## How it works

```
SOURCE DOCUMENTS (specs, meetings, emails)
  │
  ├─ Split into clauses (deterministic)
  ├─ Extract traces (LLM, max 3 iterations)
  ├─ Match traces against target (LLM)
  ├─ [--reverse] Reverse trace: target → source (LLM)
  │
  ▼
trace-map.json → LSP → Editor annotations (Zed, VS Code)
```

Two layers:
- **Control layer** (deterministic TypeScript): clause splitting, validation, remainder tracking, finalization
- **Semantic layer** (LLM via Claude Code subagents): extraction, coverage matching, reverse tracing

## Install

```bash
npm install -g @set-trace/cli
```

## Quick start

### As a Claude Code skill

```bash
# Install commands into your project
set-trace init

# Run forward pipeline
/set:trace source.md target.md

# Forward + reverse (detect unsupported claims in target)
/set:trace source.md target.md --reverse

# Custom preset
/set:trace source.md target.md --preset contract-compliance
```

### CLI commands

```bash
set-trace split source.md                          # Split into clauses
set-trace extract-prompt clauses.json --source source.md --preset spec-coverage
set-trace extract-validate output.txt clauses.json --source source.md --preset spec-coverage
set-trace remainder clauses.json traces.json       # Check uncovered clauses
set-trace match-prompt traces.json target.md --preset spec-coverage
set-trace match-validate output.txt traces.json --preset spec-coverage
set-trace finalize traces.json matches.json --source source.md --target target.md -o trace-map.json
set-trace presets                                  # List available presets
```

## Presets

Presets define domain vocabulary (trace types, coverage statuses) and prompt templates. Switch presets for different comparison types without code changes.

| Preset | Description |
|--------|-------------|
| `spec-coverage` (default) | Source requirements → target spec coverage |

Custom presets: place `./presets/<name>.json` in your project.

See [docs/presets.md](docs/presets.md) for format and examples.

## Output

`trace-map.json` — consumed by the LSP server for inline editor annotations.

Coverage markers per trace:
- **COVERED** — target fully addresses the requirement
- **PARTIAL** — partially addressed, something missing
- **MISSING** — not addressed at all
- **DEFERRED** — explicitly out of scope
- **N/A** — meta-statement, doesn't need coverage

## Documentation

| Document | Description |
|----------|-------------|
| [Presets](docs/presets.md) | Preset format, customization, discovery |
| [Benchmarks](docs/benchmarks.md) | Extraction method comparison and scoring |
| [Testing](docs/testing.md) | Test fixtures, running tests, adding ground truth |

## Development

```bash
git clone https://github.com/tatargabor/set-trace.git
cd set-trace
npm install
npm run build
npm test
```

| Command | What it does |
|---------|-------------|
| `npm run build` | Compile TypeScript |
| `npm run dev` | Watch mode |
| `npm test` | Run tests (vitest) |
| `npm run lint` | Type-check without emit |
| `npm run clean` | Remove dist/ |

### Publishing

```bash
./scripts/publish.sh patch   # bump → build → test → npm publish → git tag → GH release
./scripts/publish.sh minor
./scripts/publish.sh major
./scripts/publish.sh --dry-run patch  # preview without changes
```

Requires clean working tree, `gh` CLI, and npm auth.

## License

MIT
