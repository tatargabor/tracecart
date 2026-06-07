## Why

The core engine produces trace-map.json, but without editor integration the user must read raw JSON to understand coverage. The LSP server makes coverage visible where people actually work — in their editor. Sentences glow green/yellow/red, click-to-navigate jumps between source and target, and code lens shows per-section summaries.

This replaces the need for a custom UI, Obsidian setup, or any separate tool. Open a file → see the coverage instantly.

## Context & Key Decisions

### Why LSP, not a custom UI or Obsidian

We explored several visualization approaches:
- **Meld-style side-by-side**: doesn't scale past ~50 traces (spaghetti connections)
- **Obsidian annotated markdown**: hard to mark hundreds of cross-references interactively, link-soup at scale
- **Custom HTML viewer**: works but requires building+maintaining a separate application
- **Matrix/heatmap**: good for analysis but not for daily editing workflow

**The insight:** this is the same problem as **code coverage**. Istanbul/nyc produces coverage.json → VS Code extension colors lines green/red. We produce trace-map.json → LSP server colors sentences green/yellow/red. No custom UI needed — the editor IS the UI.

### Why LSP, not editor-specific plugin

LSP (Language Server Protocol) is universal:

| Editor | LSP support |
|--------|-------------|
| Zed | native, excellent |
| VS Code | native |
| Neovim | native |
| Emacs | lsp-mode |
| Sublime | LSP plugin |
| JetBrains | plugin |

One LSP server → every editor. No per-editor plugin maintenance.

### Why Zed first

- Native LSP support, modern, fast
- Growing developer adoption
- Extension system is simpler than VS Code
- VS Code comes second (larger audience but more complex extension API)

### The trace-map.json → LSP pipeline

```
Pipeline run (user/agent)
    → trace-map.json (on disk)
        → LSP server reads it
            → Editor shows diagnostics (colors)
            → Go to Definition (source → target navigation)
            → Find References (target → source navigation)  
            → Code Lens (per-section summaries)

Pipeline re-run → trace-map.json updated → LSP hot-reloads → editor refreshes
```

### What the user sees in the editor

Source document:
```
┌─ source/meeting-2024-01.md ─────────────────────────────────┐
│                                                              │
│ [tracecart] 8 traces: 5 ✓  2 ⚠  1 ✗          ← code lens  │
│ ## 9.3 Visszaigazolás                                        │
│                                                              │
│ ███ A visszaigazolás figyelembe veszi a CNC kapacitást  ← green (COVERED)
│ ███ Készleten lévő alapanyag esetén azonnali válasz     ← green (COVERED)
│ ███ Nem teljesíthető határidő: alternatív ajánlat       ← yellow (PARTIAL)
│ ███ Döntési logika: mikor kell projektvezetői jóváhagyás ← red (MISSING)
│                                                              │
│ Ctrl+Click on green line → jumps to target spec section      │
└──────────────────────────────────────────────────────────────┘
```

Target document:
```
┌─ specs/03-confirmation.md ──────────────────────────────────┐
│                                                              │
│ ## §2.2 CNC kapacitás                                        │
│                                                              │
│ Right-click → "Find References" → shows all source traces    │
│ that point to this section                                   │
└──────────────────────────────────────────────────────────────┘
```

### Stale detection

If the user edits a source file after the pipeline ran, line numbers may have shifted. The LSP detects this (source file mtime > trace-map.json mtime) and downgrades diagnostics to Hint with "[stale]" prefix. User re-runs pipeline to refresh.

### Hot reload

LSP polls trace-map.json mtime every 2 seconds. When it changes → re-read → update diagnostics for all open files. No server restart needed, no editor restart needed.

### Only one dependency

The entire tracecart project has zero external Python dependencies. The LSP server is the single exception: it needs `pygls` (pip install pygls). That's it.

## What Changes

- Implement a production-ready LSP server that reads trace-map.json and provides diagnostics, navigation, and code lens
- Create a Zed extension configuration that registers the LSP server for markdown files
- Implement bidirectional navigation: source→target (go to definition) and target→source (find references)
- Add hot-reload: when trace-map.json changes on disk, update diagnostics without restart
- Add stale detection: warn when source files are newer than trace-map.json
- VS Code extension as secondary target (after Zed works)

## Capabilities

### New Capabilities
- `lsp-server`: Production LSP server providing diagnostics (color by status), go-to-definition (source→target), find-references (target→source), and code-lens (inline summaries per section)
- `zed-extension`: Zed editor extension configuration that activates the LSP for markdown/text files in projects with a trace-map.json
- `hot-reload`: Mtime-based polling that re-reads trace-map.json when it changes and pushes updated diagnostics to the editor within 3 seconds

### Modified Capabilities

(none)

## Impact

- `lsp/server.py` — existing skeleton, needs production implementation
- `lsp/zed-extension/` — new Zed extension manifest and config
- Dependency: pygls (pip install pygls) — the only external dependency in the project
- Depends on: `01-core-engine` must be complete — LSP reads trace-map.json
