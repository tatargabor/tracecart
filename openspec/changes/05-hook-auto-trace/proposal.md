## Why

LLM agents can incorporate new information into documents (e.g., meeting notes into a design), but they cannot reliably self-verify completeness. They may miss source claims or hallucinate unsupported content. Asking the LLM to re-check doesn't solve this — the tool exists precisely because LLMs are unreliable at exhaustive verification.

tracecart should work as an **invisible crutch**: automatically running after the LLM finishes its work, detecting gaps and unsupported claims, and feeding results back so the LLM can correct itself — without the user needing to know or explicitly invoke anything.

## What Changes

- Introduce a Claude Code hook that triggers at command boundary (turn end), detects whether trace-relevant files changed, and runs the tracecart pipeline automatically
- Add a project-level configuration for source↔target file mappings so the hook knows which files to trace
- Implement a result feedback mechanism that injects trace findings into the LLM's next turn context
- Provide a CLI entrypoint (`tracecart check`) for non-hook usage (CI, manual runs, other agent frameworks)

## Capabilities

### New Capabilities

- `hook-trigger`: Claude Code hook that detects trace-relevant file changes via git diff at turn boundary and triggers the tracecart pipeline when source or target files were modified
- `trace-config`: Project-level configuration defining source↔target file mappings, used by the hook to determine when a trace run is needed
- `trace-feedback`: Mechanism for feeding trace results (MISSING, PARTIAL, UNTRACED_IN_SOURCE) back to the LLM context so it can act on findings
- `trace-cli`: CLI entrypoint for running the trace pipeline outside of hooks (manual invocation, CI integration, other agent frameworks)

### Modified Capabilities

(none — this change builds on top of the engine, does not modify it)

## Impact

- `.claude/settings.json` or `.claude/hooks/`: hook registration
- `.tracecart/config.json` (or similar): new project config file for source↔target mappings
- `src/` or `bin/`: CLI entrypoint script
- Dependencies: none added (Python stdlib, Claude Code hook system)
- Depends on: `01-core-engine` (extraction + forward matching) and `02-reverse-trace` (bidirectional matching)
