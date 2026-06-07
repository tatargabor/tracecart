# Contributing to tracecart

## Dev Setup

```bash
git clone https://github.com/tatargabor/tracecart.git
cd tracecart
npm install
npm run build
```

## Commands

| Command | What it does |
|---------|-------------|
| `npm run build` | Compile TypeScript to dist/ |
| `npm run dev` | Watch mode (rebuild on change) |
| `npm test` | Run unit tests (vitest) |
| `npm run test:watch` | Watch mode for tests |
| `npm run lint` | Type-check without emitting |
| `npm run clean` | Remove dist/ |

## Project structure

```
src/                  TypeScript source
  cli.ts              Entry point, argument parsing
  preset.ts           Preset loading/validation
  parse/              Clause splitting, document parsing
  extract/            Trace extraction + validation
  match/              Coverage matching + reverse tracing
  output/             trace-map.json generation
  commands/           CLI subcommand handlers
presets/              Built-in preset JSON files
prompts/              LLM prompt templates
templates/            Claude Code command markdown
tests/                Test files (vitest)
  fixtures/           Source/target document pairs
docs/                 Documentation
scripts/              Publish and utility scripts
```

## Conventions

- TypeScript, zero runtime dependencies
- Node.js >= 18, ESM only
- All deterministic code: stdin/stdout JSON, testable offline
- LLM calls go through Claude Code subagents, never direct SDK
- Prompt templates in `prompts/` — plain text, `{variable}` placeholders
- Presets in `presets/` — JSON, no YAML

## Adding a CLI command

1. Create `src/commands/<name>.ts` with an exported `cmd<Name>` function
2. Add the case to `src/cli.ts` switch statement
3. Add to the `cmds` array in `printUsage()`

## Adding a preset

1. Create `presets/<name>.json` with the required fields (see docs/presets.md)
2. The preset is automatically discovered by `tracecart presets`

## Tests

- Place test files as `tests/<name>.test.ts`
- Fixtures go in `tests/fixtures/<name>/`
- Run with `npm test`

## Publishing

Only maintainers publish. Use the publish script:

```bash
./scripts/publish.sh patch
```

This bumps the version, builds, runs tests, publishes to npm, tags, and creates a GitHub release.
