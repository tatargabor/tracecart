## 1. Status bar summary

- [x] 1.1 Add status bar item to VS Code extension that reads trace-map.json summary
- [x] 1.2 Format display: "tracecart: 79.7% | 24✓ 3⚠ 5✗" with reverse if present
- [x] 1.3 Click action opens Problems panel
- [x] 1.4 Auto-refresh on trace-map.json file change via existing watcher

## 2. Delta command

- [x] 2.1 Create `src/output/delta.py` with compare function: two trace-map dicts → delta result
- [x] 2.2 ID-based matching with text-similarity fallback for shifted traces
- [x] 2.3 Categorize changes: improved, regressed, new, removed, unchanged
- [x] 2.4 Summary statistics: old% → new% (+diff)
- [x] 2.5 Register `delta` subcommand in `src/run_trace.py`
- [x] 2.6 Support `--json` flag for machine-readable output
