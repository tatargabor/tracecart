# Presets

Presets decouple domain-specific configuration from the pipeline code. A preset defines what types of traces to extract, what coverage statuses to use, and which prompt templates to load.

## Format

```json
{
  "name": "spec-coverage",
  "description": "Source requirements → target spec coverage verification",
  "version": "1.0",
  "trace_types": ["REQUIREMENT", "DECISION", "WISH", "OPEN_QUESTION", "EXCLUSION"],
  "coverage_statuses": ["COVERED", "PARTIAL", "MISSING", "DEFERRED", "N/A"],
  "prompts": {
    "extract": "extract.txt",
    "coverage_check": "coverage_check.txt",
    "reverse_check": "reverse_check.txt"
  },
  "defaults": {
    "language": "en"
  }
}
```

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier for the preset |
| `trace_types` | string[] | Valid trace types the LLM can assign |
| `coverage_statuses` | string[] | Valid coverage statuses for matching |
| `prompts` | object | Maps prompt roles to filenames in `prompts/` |

### Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Human-readable description (shown by `set-trace presets`) |
| `version` | string | Semantic version of the preset |
| `defaults` | object | Default values (currently: `language`) |

## Discovery order

1. **Project-local**: `./presets/<name>.json` (highest priority)
2. **Built-in**: `<package>/presets/<name>.json`

Project-local presets override built-in ones by name.

## Built-in presets

### spec-coverage (default)

The default preset. Extracts requirements from source documents and verifies coverage in target specs.

- **Trace types**: REQUIREMENT, DECISION, WISH, OPEN_QUESTION, EXCLUSION
- **Coverage statuses**: COVERED, PARTIAL, MISSING, DEFERRED, N/A
- **Use case**: Meeting notes / client specs → functional specification coverage

## Creating a custom preset

1. Create `presets/<name>.json` in your project root
2. Define trace types relevant to your domain
3. Define coverage statuses meaningful for your verification
4. Reference prompt templates (use built-in `prompts/*.txt` or write custom ones)

### Example: contract compliance

```json
{
  "name": "contract-compliance",
  "description": "Contract clauses → implementation verification",
  "version": "1.0",
  "trace_types": ["OBLIGATION", "PROHIBITION", "PERMISSION", "CONDITION"],
  "coverage_statuses": ["FULFILLED", "PARTIAL", "VIOLATED", "WAIVED", "N/A"],
  "prompts": {
    "extract": "extract.txt",
    "coverage_check": "coverage_check.txt",
    "reverse_check": "reverse_check.txt"
  }
}
```

### Example: test coverage

```json
{
  "name": "test-coverage",
  "description": "Requirements → test case coverage verification",
  "version": "1.0",
  "trace_types": ["FUNCTIONAL", "NON_FUNCTIONAL", "EDGE_CASE", "ERROR_HANDLING"],
  "coverage_statuses": ["TESTED", "PARTIAL", "UNTESTED", "OUT_OF_SCOPE", "N/A"],
  "prompts": {
    "extract": "extract.txt",
    "coverage_check": "coverage_check.txt",
    "reverse_check": "reverse_check.txt"
  }
}
```

## How presets interact with prompts

Prompt templates use `{trace_types}` and `{coverage_statuses}` placeholders. At runtime, these are replaced with the active preset's values joined by ` | `.

For example, with the `contract-compliance` preset, the extraction prompt will contain:
```
type: OBLIGATION | PROHIBITION | PERMISSION | CONDITION
```

The built-in prompt templates (`prompts/*.txt`) work with any preset — no custom prompts needed unless you want specialized extraction instructions.
