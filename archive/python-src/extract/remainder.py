#!/usr/bin/env python3
"""Recursive remainder tracker for trace extraction.

Tracks which clauses have been "consumed" by extracted traces,
computes the remainder (untraced clauses), and determines
when extraction is complete.

The LLM is never trusted for completeness — this module
provides deterministic termination control.
"""

import json
import sys
from pathlib import Path


def compute_remainder(clauses: list[dict], traces: list[dict]) -> list[dict]:
    """Compute untraced clauses (set difference).

    Args:
        clauses: all input clauses [{clause_id, text, ...}]
        traces: extracted traces [{clause_id, ...}] (each references source clause)

    Returns:
        List of clauses not referenced by any trace.
    """
    traced_ids = set()
    for trace in traces:
        if 'clause_id' in trace:
            traced_ids.add(trace['clause_id'])
        if 'clause_ids' in trace:
            traced_ids.update(trace['clause_ids'])

    remainder = [c for c in clauses if c['clause_id'] not in traced_ids]
    return remainder


def is_complete(remainder: list[dict], previous_remainder: list[dict] | None) -> bool:
    """Determine if extraction should terminate.

    Terminal conditions:
    1. Remainder is empty (all clauses consumed)
    2. Remainder did not shrink since last iteration (LLM cannot extract more)
    """
    if not remainder:
        return True

    if previous_remainder is not None:
        if len(remainder) >= len(previous_remainder):
            return True

    return False


def extraction_stats(clauses: list[dict], traces: list[dict], remainder: list[dict]) -> dict:
    """Compute extraction statistics."""
    return {
        'total_clauses': len(clauses),
        'traces_extracted': len(traces),
        'clauses_consumed': len(clauses) - len(remainder),
        'clauses_remaining': len(remainder),
        'coverage_pct': (len(clauses) - len(remainder)) / len(clauses) * 100 if clauses else 0,
        'complete': len(remainder) == 0,
    }


def main():
    """CLI: compute remainder from clauses JSON and traces JSON."""
    if len(sys.argv) < 3:
        print("Usage: remainder.py <clauses.json> <traces.json>", file=sys.stderr)
        print("  Outputs: remainder clauses + stats as JSON", file=sys.stderr)
        sys.exit(1)

    clauses = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    traces = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

    if isinstance(clauses, dict) and 'clauses' in clauses:
        clauses = clauses['clauses']
    if isinstance(traces, dict) and 'traces' in traces:
        traces = traces['traces']

    remainder = compute_remainder(clauses, traces)
    stats = extraction_stats(clauses, traces, remainder)

    output = {
        'stats': stats,
        'remainder': remainder,
    }

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
