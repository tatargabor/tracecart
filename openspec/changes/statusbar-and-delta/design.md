## Context

A VS Code extension jelenleg soronkénti színezést, code lens szekció-összesítőt és hover navigációt biztosít. Macro-szintű áttekintés (coverage %) és futások közötti delta összehasonlítás nincs. Az LLM auto-iteráció igényli a gépi olvasható delta outputot.

## Goals / Non-Goals

**Goals:**
- Status bar-ban azonnal látható coverage összesítő
- Két trace-map.json közötti delta számítás CLI parancsként
- Delta output JSON (gépi) és human-readable (emberi) formátumban

**Non-Goals:**
- WebView/sidebar panel (későbbi feature)
- Delta vizualizáció VS Code-ban (egyelőre csak CLI)
- Történeti delta lánc (trace-map verziózás)

## Decisions

**Status bar implementáció**: `vscode.window.createStatusBarItem` a trace-map.json summary mezőjéből. A trace-map.json-t az extension már betölti — a summary mező tartalmazza a coverage számokat, nem kell újraszámolni.

**Delta algoritmus**: trace ID alapú összevetés — a trace ID-k determinisztikusak (fájlnév hash + sor), ezért futások között stabilak ha a source nem változott. Státusz-átmenetek kategorizálása: javult (MISSING→PARTIAL/COVERED, PARTIAL→COVERED), romlott (fordítva), új trace, eltűnt trace.

**Delta output formátum**: JSON a `--json` flag-gel, human-readable text alapértelmezetten. A JSON-t az LLM agent közvetlenül feldolgozza, a text-et az ember olvassa a CLI-ben.

## Risks / Trade-offs

Trace ID instabilitás ha a source fájl változik (sorok eltolódnak) → a delta hamis "eltűnt + új" párosokat mutathat. Mitigáció: a trace text-re is matchelünk fallback-ként.
