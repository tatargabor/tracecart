# Hook-based Automatic Trace Verification — Planning Brief

## Kontextus

A **tracecart** projekt egy claim traceability tool: source dokumentumokból (meeting notes, emailek) atomi trace-eket extraktál, és ellenőrzi hogy egy target dokumentum (design, spec) teljesen lefedi-e őket. A pipeline: PARSE → EXTRACT → MATCH → OUTPUT → `trace-map.json`. LSP szerveren keresztül vizualizál editorban.

Van egy meglévő OpenSpec change (`core-engine-v1`) ami a v1 pipeline-t definiálja — forward trace only (source→target). A kód részben kész: clause_split, parse_document, discover_inputs, remainder tracker skeleton, trace_map output skeleton. Az extract és match modulok még implementálandók.

Lásd: `DESIGN.md` (teljes architektúra), `openspec/changes/core-engine-v1/` (meglévő change artifactok).

## Motiváció

Az LLM agent kap egy feladatot (pl. "tervezd bele ezt a meeting notes-t a designba"), megcsinálja a legjobb tudása szerint, de **nem tudja visszaellenőrizni** hogy 100%-ban lefedett-e mindent. Ha megkérjük sem fogja tudni — azért írjuk a toolt, mert az LLM alapból tévedhet.

A tracecart-nek **invisible crutch**-ként kell működnie: a felhasználó nem tudja hogy fut, nem kell explicit hívni. Csak azt tapasztalja hogy az LLM megbízhatóbban dolgozik.

## Két egymásra épülő change kell

---

### Change 1: Reverse trace (bidirectional trace) — engine kiegészítés

A `core-engine-v1` a reverse trace-t explicit non-goal-nak jelöli ("v2"). Ez hiba volt. A matching során a pipeline **már végigmegy** a target section-ökön — azok az állítások amik a targetben vannak de egyetlen source trace-hez sem köthetők, gyakorlatilag "ingyen" kijönnek.

#### Amit a bidi trace ad

| Irány | Kérdés | Eredmény |
|-------|--------|----------|
| **Forward** (source→target) | "Mindent lefedett a target?" | COVERED / PARTIAL / MISSING |
| **Reverse** (target→source) | "Minden ami a targetben van, az source-ból jön?" | `UNTRACED_IN_SOURCE` |

#### Az `UNTRACED_IN_SOURCE` jelentése

A target tartalmaz egy állítást ami nem vezethető vissza egyetlen source dokumentumra sem. Ez lehet:
- **Hallucináció** — az LLM kitalálta
- **Kreatív kiegészítés** — az LLM jó dolgot talált ki ami nem volt a source-ban
- **Más source-ból jön** — amit a rendszer nem ismer

A felhasználó dönti el melyik — a tool csak jelzi.

#### Implementáció

A reverse trace lényegében ugyanaz a pipeline visszafelé futtatva:
1. A target-ből is kell trace-eket extraktálni (ugyanaz az extract pipeline)
2. Ellenőrizni hogy visszavezethetőek-e a source trace-ekre (ugyanaz a matching, fordított irányban)
3. A `trace-map.json` output-ba az `UNTRACED_IN_SOURCE` trace-ek is belekerülnek, külön szekció

#### Kérdés a tervezőnek

A reverse trace a `core-engine-v1` change amendment-je legyen, vagy külön change?

---

### Change 2: Hook integration — automatikus trace verification

#### Use case

```
┌──────────────────────────────────────────────────────────────────┐
│  JELENLEGI WORKFLOW (kézi, megbízhatatlan)                      │
│                                                                  │
│  meeting-notes-new.md  ──▶  LLM agent  ──▶  design.md (updated) │
│                              "tervezd bele"     ✓ legjobb tudása│
│                                                  ✗ nem ellenőrzi│
│                                                  ✗ kihagyhat    │
│                                                  ✗ hallucinate  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  KÍVÁNT WORKFLOW (automatikus, zárt hurok)                       │
│                                                                  │
│  meeting-notes-new.md  ──▶  LLM agent  ──▶  design.md (updated) │
│                              "tervezd bele"          │           │
│                                                      ▼           │
│                                              ┌──────────────┐   │
│                                              │  HOOK         │   │
│                                              │  tracecart    │   │
│                                              │  runs auto    │   │
│                                              └──────┬───────┘   │
│                                                      │           │
│                                              trace-map.json      │
│                                              "3 MISSING,         │
│                                               1 UNTRACED"       │
│                                                      │           │
│                                                      ▼           │
│                                              LLM reads results   │
│                                              ──▶ corrects design │
│                                              ──▶ loop until 100% │
└──────────────────────────────────────────────────────────────────┘
```

#### Trigger mechanizmus

- **Mikor:** Command boundary — amikor az LLM végzett az összes műveletével és a userre vár. Claude Code-ban ez a teljes turn vége.
- **Mit vizsgál:** `git diff --name-only` — mi változott a turn során?
- **Mikor fut:** Ha a változott fájlok között van regisztrált source VAGY target fájl. Ehhez kell egy project-szintű konfig ami definiálja a source↔target mapping-ot.
- **Mikor NEM fut:** Ha a változások nem érintenek trace-relevant fájlokat → skip, semmi overhead.

#### Config

```json
// .tracecart/config.json (vagy más helyen — tervező döntse el)
{
  "mappings": [
    {
      "sources": ["meetings/*.md", "emails/*.md"],
      "targets": ["design.md", "specs/*.md"]
    }
  ]
}
```

#### Hook flow

```
LLM dolgozik → editál → kész
        │
        ▼
   HOOK TRIGGER (turn vége)
        │
        ▼
   git diff → változott-e source/target?
        │
    ┌───┴───┐
    │ nem   │ igen
    │ skip  │
    └───────┘   │
                ▼
        tracecart pipeline fut
        (forward + reverse)
                │
                ▼
        trace-map.json eredmény
                │
                ▼
        Eredmény visszamegy az LLM-nek
        a KÖVETKEZŐ turn context-jében:
        "3 MISSING, 1 PARTIAL, 2 UNTRACED_IN_SOURCE"
                │
                ▼
        LLM eldönti: javít, vagy jelzi a usernek
```

#### Nyitott design kérdések a tervezőnek

1. **Hook eredmény visszaadás:** Hogyan jusson vissza az LLM-hez? Opciók:
   - Hook stdout → az LLM a következő turnben látja mint context
   - A `trace-map.json`-ra mutat és az LLM felolvassa
   - Summary szöveg a lényeges finding-ekkel

2. **Config formátum és helye:**
   - `.tracecart/config.json`?
   - `CLAUDE.md`-be annotáció?
   - Más?

3. **Pipeline futási idő:** Jelentős lehet — kell-e async/background mód ahol a hook nem blokkolja a usert?

4. **Scope:** A hook csak Claude Code hook-ként működjön, vagy legyen CLI is (`tracecart check`) amit bármilyen CI/hook rendszerből hívhatunk?

## Függőségek

```
core-engine-v1 (extraction + forward matching + output)
        │
        ▼
Change 1: reverse trace (bidi)
        │
        ▼
Change 2: hook integration
```

A hook change függ attól hogy a core engine működjön (extraction + matching + output), beleértve a reverse trace-t.
