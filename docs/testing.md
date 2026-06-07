# Testing

## Running tests

```bash
npm test              # Run all tests once
npm run test:watch    # Watch mode
npx vitest run tests/preset.test.ts  # Run specific test file
```

## Test structure

```
tests/
  preset.test.ts      — Preset loading, validation, discovery
  fixtures/
    test1/            — Basic source/target pair
      source.md
      target.md
      trace-map.json  — Expected output (reference)
    test2/            — Second fixture set
      source.md
      target.md
```

## Test fixtures

Fixtures in `tests/fixtures/` are real document pairs with known trace-maps. They serve as regression tests for the deterministic pipeline steps (split, validate, finalize).

### Adding a new fixture

1. Create `tests/fixtures/<name>/source.md` and `target.md`
2. Run the full pipeline to generate `trace-map.json`
3. Manually review the trace-map for correctness
4. Commit as the expected output

## What's tested

### Unit tests (deterministic, fast)

- **Preset system**: loading, validation, discovery, listing
- **Clause splitter**: line numbering, compound sentence detection, header handling
- **Validation**: trace type checking, coverage status checking, JSON parsing
- **Remainder**: coverage calculation, uncovered clause detection
- **Finalize**: trace-map assembly, ref resolution

### Integration tests (require LLM, slow)

Not automated — run manually via the `/tracecart` skill on fixture data. The LLM output varies between runs, but the deterministic validation catches structural issues.

## Adding tests

Tests use [Vitest](https://vitest.dev/). Place test files as `tests/<name>.test.ts`.

```typescript
import { describe, it, expect } from 'vitest';

describe('my feature', () => {
  it('does the thing', () => {
    expect(myFunction(input)).toEqual(expected);
  });
});
```

The `tsconfig.json` excludes `tests/` from compilation — Vitest handles TypeScript transformation separately.
