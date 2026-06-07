## Context

tracecart has an extraction + matching pipeline (01-core-engine) and bidirectional trace support (02-reverse-trace). These produce `trace-map.json` from source + target documents. Currently, running the pipeline requires explicit invocation.

The goal is to make tracecart run **automatically** as a Claude Code hook — invisible to the user. The LLM works, the hook verifies, results feed back, the LLM corrects. A closed loop where the user only sees better output.

Claude Code hooks are shell commands that run at specific lifecycle events. They can be configured in `.claude/settings.json` under `hooks`. The relevant hook points:
- `PostToolCall` — after each tool call (too granular)
- `Stop` — when the agent finishes its turn and is about to return to the user (this is the right trigger point)

## Goals / Non-Goals

**Goals:**
- Automatic trace verification at turn boundary — no user action needed
- Git-diff-based change detection to avoid unnecessary pipeline runs
- Project config for source↔target mapping (which files to trace)
- Result feedback to LLM context for self-correction
- CLI entrypoint for non-hook usage

**Non-Goals:**
- Real-time tracing during LLM operation (too slow, would block the agent)
- Modifying the core pipeline (this change wraps it, doesn't change it)
- Automatic correction by the hook itself (the hook reports, the LLM decides)
- Supporting non-Claude-Code agent frameworks in v1 (CLI covers basic interop)

## Decisions

### 1. Hook trigger: `Stop` event, not `PostToolCall`

The hook runs at the `Stop` event — when the agent has finished all tool calls and is about to return control to the user. Not after every individual file write.

**Rationale:** Running after each `Write`/`Edit` would trigger multiple times per turn, on intermediate states. The `Stop` event sees the final state of all changes. It also doesn't slow down the agent's work — the trace runs after the agent is done.

**Alternative considered:** `PostToolCall` with debouncing. Rejected: complex, still runs on intermediate states, and the hook system doesn't natively support debouncing.

### 2. Change detection: `git diff --name-only` against registered mappings

The hook script:
1. Runs `git diff --name-only` (unstaged) + `git diff --name-only --cached` (staged)
2. Checks changed files against the source↔target mappings in config
3. If any mapped file changed → run pipeline
4. If no mapped file changed → exit 0, no output, invisible

```bash
# Pseudocode
changed=$(git diff --name-only && git diff --name-only --cached)
if matches_any_mapping "$changed" "$config"; then
    run_trace_pipeline
else
    exit 0  # silent skip
fi
```

**Rationale:** Git diff is fast (<10ms), reliable, and captures exactly what changed since the last clean state. No file watchers, no state tracking.

**Edge case:** If the user manually edited files outside Claude Code, those show up in git diff too. This is correct behavior — trace should verify regardless of who made the change.

### 3. Config: `.tracecart/config.json` in project root

```json
{
  "mappings": [
    {
      "name": "order-intake",
      "sources": ["meetings/*.md", "emails/*.md"],
      "targets": ["specs/order-intake.md"]
    },
    {
      "name": "confirmation",
      "sources": ["meetings/*.md", "requirements/**/*.md"],
      "targets": ["specs/confirmation.md", "specs/confirmation-*.md"]
    }
  ]
}
```

**Rationale:** Separate file (not in CLAUDE.md or .claude/settings.json) because:
- It's project-specific, not agent-specific
- It might be used by CI, other agents, or the CLI
- Glob patterns for file matching are more natural in JSON than embedded in markdown
- It can be version-controlled

**The `name` field** identifies the mapping for human-readable output ("order-intake: 3 MISSING").

### 4. Result feedback: hook stdout → LLM context

Claude Code hooks can return output that gets injected into the conversation. The hook prints a structured summary to stdout:

```
[tracecart] order-intake: 98.5% coverage (2 MISSING, 1 PARTIAL)
  MISSING: T-a3f2c1-012 — CNC kapacitás constraint
  MISSING: T-a3f2c1-034 — szállítási határidő
  PARTIAL: T-a3f2c1-027 — felületkezelési idő (only lacquering mentioned)
  UNTRACED: RT-b2d4e7-012 — "max 48h visszaigazolás" not in any source
[tracecart] Full results: .tracecart/output/order-intake/trace-map.json
```

The LLM sees this in its next turn and can:
- Incorporate the MISSING traces
- Investigate the UNTRACED claims (keep or remove)
- Re-run (the hook will trigger again on the next turn if files change)

**Rationale:** Stdout is the simplest feedback channel. The summary is human-readable AND LLM-parseable. The full trace-map.json path is included for the LLM to read if it needs details.

**Alternative considered:** Writing to a well-known file and adding a CLAUDE.md instruction to read it. Rejected: more moving parts, relies on the LLM noticing the file. Stdout is direct.

### 5. CLI entrypoint: `python3 -m set_trace check`

A CLI command that does what the hook does, but manually:

```bash
python3 -m set_trace check                    # all mappings in config
python3 -m set_trace check --mapping order-intake  # specific mapping
python3 -m set_trace check --source meetings/2024-03-15.md --target specs/order-intake.md  # ad-hoc
```

**Rationale:** The hook is just an automation wrapper. The actual logic should be callable independently for CI, debugging, and other agent frameworks.

### 6. Pipeline caching: skip if inputs unchanged

The hook stores a hash of source+target file contents in `.tracecart/cache/`. If the hash matches the previous run, skip the pipeline.

```
.tracecart/
├── config.json
├── cache/
│   └── order-intake.hash    # sha256 of all source+target contents
└── output/
    └── order-intake/
        └── trace-map.json   # latest result
```

**Rationale:** The pipeline involves LLM calls and can take 30-60 seconds. If files didn't change since the last trace run, the previous result is still valid. Git diff detects file changes cheaply, but the cache provides a second layer: even if git shows changes (e.g., unstaged from a previous turn), the hash catches that the content is the same as the last run.

## Risks / Trade-offs

**[Risk] Pipeline is too slow for interactive use** — 30-60s for extraction + matching at current scale.
→ Mitigation: The hook runs at `Stop`, when the user is reading output anyway. The trace result appears before the user types their next message. At larger scale, consider background execution with results appearing asynchronously.

**[Risk] Hook stdout floods the LLM context** — many mappings with many findings could produce a lot of output.
→ Mitigation: Summary-first format. Only top-level stats + individual MISSING/UNTRACED items. Full details in trace-map.json file. Cap stdout to top 10 findings per mapping.

**[Risk] False positive UNTRACED claims** — target boilerplate, structural content, or cross-domain knowledge gets flagged.
→ Mitigation: Meta-content filtering (from `02-reverse-trace`). Config option to suppress specific trace IDs once reviewed. The user/LLM decides what to act on.

**[Risk] Hook fires unnecessarily** — e.g., editing a README that matches a glob pattern.
→ Mitigation: Content-hash cache means the pipeline won't re-run if the relevant files haven't changed. Narrow glob patterns in config. Cost of a false trigger is only the git diff + hash check time (~50ms).
