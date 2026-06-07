#!/usr/bin/env python3
"""Generate trace-map.json from extraction and matching results.

This is the universal output format consumed by:
- LSP server (editor visualization)
- HTML viewer (if built later)
- Any downstream tool

The trace-map is the single source of truth for all visualization.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TRACE_MAP_VERSION = 1


def build_trace_map(
    traces: list[dict],
    source_files: list[str],
    target_files: list[str],
    untraced_clauses: list[dict] | None = None,
    metadata: dict | None = None,
    reverse_traces: list[dict] | None = None,
) -> dict:
    """Build a trace-map.json structure.

    Args:
        traces: list of trace dicts, each with:
            - id, text, type, source (file/line/col), status, refs, topics, etc.
        source_files: list of source file paths
        target_files: list of target file paths
        untraced_clauses: clauses not consumed by any trace (from remainder tracker)
        metadata: optional extra metadata
        reverse_traces: target-extracted claims with reverse traceability status

    Returns:
        Complete trace-map dict ready for JSON serialization.
    """
    summary = compute_summary(traces, reverse_traces)

    trace_map = {
        'version': TRACE_MAP_VERSION,
        'generated': datetime.now(timezone.utc).isoformat(),
        'source_files': source_files,
        'target_files': target_files,
        'traces': traces,
        'untraced_clauses': [
            {'clause_id': c.get('clause_id', ''), 'text': c.get('text', '')}
            for c in (untraced_clauses or [])
        ],
        'summary': summary,
    }

    if reverse_traces is not None:
        trace_map['reverse_traces'] = reverse_traces

    if metadata:
        trace_map['metadata'] = metadata

    return trace_map


def compute_summary(traces: list[dict], reverse_traces: list[dict] | None = None) -> dict:
    """Compute coverage summary from traces list, optionally including reverse stats."""
    status_counts = {}
    for trace in traces:
        status = trace.get('status', 'UNKNOWN')
        status_counts[status] = status_counts.get(status, 0) + 1

    total = len(traces)
    covered = status_counts.get('COVERED', 0)
    partial = status_counts.get('PARTIAL', 0)
    missing = status_counts.get('MISSING', 0)

    checkable = covered + partial + missing
    score = (covered + partial * 0.5) / checkable * 100 if checkable > 0 else 0

    summary = {
        'total': total,
        'covered': covered,
        'partial': partial,
        'missing': missing,
        'deferred': status_counts.get('DEFERRED', 0),
        'superseded': status_counts.get('SUPERSEDED', 0),
        'na': status_counts.get('N/A', 0),
        'coverage_score_pct': round(score, 1),
    }

    if reverse_traces is not None:
        rev_counts = {}
        for rt in reverse_traces:
            st = rt.get('status', 'UNKNOWN')
            rev_counts[st] = rev_counts.get(st, 0) + 1

        rev_traced = rev_counts.get('TRACED', 0)
        rev_partial = rev_counts.get('PARTIAL_SOURCE', 0)
        rev_untraced = rev_counts.get('UNTRACED_IN_SOURCE', 0)
        rev_checkable = rev_traced + rev_partial + rev_untraced

        rev_score = (
            (rev_traced + rev_partial * 0.5) / rev_checkable * 100
            if rev_checkable > 0 else 0
        )

        summary['reverse_total'] = len(reverse_traces)
        summary['reverse_traced'] = rev_traced
        summary['reverse_partial_source'] = rev_partial
        summary['reverse_untraced'] = rev_untraced
        summary['reverse_coverage_pct'] = round(rev_score, 1)

    return summary


def build_source_annotations(traces: list[dict]) -> dict:
    """Build per-file annotation map for source documents.

    Returns: {filepath: [{range, status, refs, trace_id}]}
    Used by LSP server to publish diagnostics on source files.
    """
    annotations = {}

    for trace in traces:
        source = trace.get('source', {})
        filepath = source.get('file')
        if not filepath:
            continue

        if filepath not in annotations:
            annotations[filepath] = []

        annotations[filepath].append({
            'range': {
                'start': {'line': source.get('line', 0), 'col': source.get('col_start', 0)},
                'end': {'line': source.get('line', 0), 'col': source.get('col_end', 0)},
            },
            'status': trace.get('status', 'UNKNOWN'),
            'trace_id': trace.get('id'),
            'trace_text': trace.get('text', ''),
            'refs': trace.get('refs', []),
        })

    return annotations


def build_target_annotations(traces: list[dict], reverse_traces: list[dict] | None = None) -> dict:
    """Build per-file annotation map for target documents.

    Returns: {filepath: [{range, trace_ids, trace_texts}]}
    Used by LSP server to publish diagnostics and references on target files.
    Includes UNTRACED_IN_SOURCE diagnostics from reverse traces.
    """
    annotations = {}

    for trace in traces:
        for ref in trace.get('refs', []):
            filepath = ref.get('file')
            if not filepath:
                continue

            if filepath not in annotations:
                annotations[filepath] = []

            annotations[filepath].append({
                'line': ref.get('line', 0),
                'section': ref.get('section', ''),
                'trace_id': trace.get('id'),
                'trace_text': trace.get('text', ''),
                'status': trace.get('status', 'UNKNOWN'),
                'source': trace.get('source', {}),
            })

    for rt in (reverse_traces or []):
        if rt.get('status') not in ('UNTRACED_IN_SOURCE', 'PARTIAL_SOURCE'):
            continue

        source = rt.get('source', {})
        filepath = source.get('file')
        if not filepath:
            continue

        if filepath not in annotations:
            annotations[filepath] = []

        annotations[filepath].append({
            'line': source.get('line', 0),
            'section': '',
            'trace_id': rt.get('id'),
            'trace_text': rt.get('text', ''),
            'status': rt.get('status'),
            'nearest_source_trace': rt.get('nearest_source_trace'),
            'similarity_note': rt.get('similarity_note', ''),
        })

    return annotations


def main():
    """CLI: build trace-map from traces JSON."""
    if len(sys.argv) < 2:
        print("Usage: trace_map.py <traces.json> [output.json]", file=sys.stderr)
        print("  traces.json must have: traces, source_files, target_files", file=sys.stderr)
        print("  Optional fields: untraced_clauses, metadata", file=sys.stderr)
        sys.exit(1)

    data = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))

    trace_map = build_trace_map(
        traces=data.get('traces', []),
        source_files=data.get('source_files', []),
        target_files=data.get('target_files', []),
        untraced_clauses=data.get('untraced_clauses', []),
        metadata=data.get('metadata'),
        reverse_traces=data.get('reverse_traces'),
    )

    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if output_path:
        output_path.write_text(
            json.dumps(trace_map, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        json.dump(trace_map, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
