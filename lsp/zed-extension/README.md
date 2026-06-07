# tracecart Zed Extension

Coverage diagnostics for claim traceability. Colors source document sentences by coverage status, enables click-to-navigate between source and target, and shows per-section summaries.

## Prerequisites

```bash
pip install pygls
```

## Setup

1. Install the extension in Zed
2. Run the tracecart pipeline to generate `trace-map.json` in your project root
3. Open any `.md` file — diagnostics appear automatically

## What you see

| Color | Meaning |
|-------|---------|
| Red underline | MISSING — source claim not found in target |
| Yellow underline | PARTIAL — target addresses part but misses specifics |
| Subtle hint | COVERED — fully addressed in target |
| Blue info | DEFERRED — out of current scope |

Above section headers: `[tracecart] 8 traces: 5 ✓  2 ⚠  1 ✗`

## Navigation

- **Go to Definition** (Ctrl+Click on source line) → jumps to target section
- **Find References** (on target section) → lists all source traces pointing here

## Hot reload

Edit or re-run the pipeline → `trace-map.json` updates → diagnostics refresh within 3 seconds. No restart needed.

## Stale detection

If you edit a source file after the pipeline ran, diagnostics show `[stale]` prefix and downgrade to hints. Re-run the pipeline to refresh.
