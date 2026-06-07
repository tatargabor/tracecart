## Why

A pipeline futtatás után nincs azonnali macro-szintű visszajelzés a coverage állapotról — a felhasználónak végig kell scrolloznia a fájlokat. Iteratív javításnál (ember vagy LLM agent) nincs mód két futás közötti változások gyors áttekintésére: mi javult, mi romlott.

## What Changes

- VS Code extension status bar item: mutatja a forward/reverse coverage %-ot és trace számokat (✓/⚠/✗), kattintásra megnyitja a Problems panelt
- Új `delta` subcommand a `run_trace.py`-ban: két trace-map.json összehasonlítása, javult/romlott/új/eltűnt trace-ek listázása
- Delta output JSON és human-readable formátumban is, az LLM auto-iteráció alapja

## Capabilities

### New Capabilities
- `statusbar-summary`: VS Code status bar coverage összesítő a trace-map.json alapján
- `trace-delta`: Két trace-map.json összehasonlítása, változások kimutatása

### Modified Capabilities

## Impact

- `lsp/vscode-extension/extension.js` — status bar item hozzáadása
- `src/run_trace.py` — új `delta` subcommand
- `src/output/` — új delta modul
