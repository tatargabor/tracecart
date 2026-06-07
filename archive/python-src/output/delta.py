#!/usr/bin/env python3
"""Compare two trace-map.json files and report what changed."""

import json
import sys
from pathlib import Path


def _build_index(traces):
    by_id = {}
    by_text = {}
    for t in traces:
        by_id[t['id']] = t
        text = t.get('text', '').strip().lower()
        if text:
            by_text[text] = t
    return by_id, by_text


def compare(old_map: dict, new_map: dict) -> dict:
    old_traces = old_map.get('traces', [])
    new_traces = new_map.get('traces', [])

    old_by_id, old_by_text = _build_index(old_traces)
    new_by_id, new_by_text = _build_index(new_traces)

    improved = []
    regressed = []
    unchanged = []
    new_items = []
    removed = []

    rank = {'COVERED': 3, 'TRACED': 3, 'PARTIAL': 2, 'PARTIAL_SOURCE': 2,
            'MISSING': 1, 'UNTRACED_IN_SOURCE': 1, 'DEFERRED': 2, 'N/A': 0}

    matched_old = set()

    for t in new_traces:
        tid = t['id']
        old_t = old_by_id.get(tid)

        if not old_t:
            text = t.get('text', '').strip().lower()
            old_t = old_by_text.get(text)

        if old_t:
            matched_old.add(old_t['id'])
            old_status = old_t.get('status', 'MISSING')
            new_status = t.get('status', 'MISSING')
            old_rank = rank.get(old_status, 0)
            new_rank = rank.get(new_status, 0)

            if new_rank > old_rank:
                improved.append({
                    'id': tid, 'text': t.get('text', ''),
                    'old_status': old_status, 'new_status': new_status,
                })
            elif new_rank < old_rank:
                regressed.append({
                    'id': tid, 'text': t.get('text', ''),
                    'old_status': old_status, 'new_status': new_status,
                })
            else:
                unchanged.append(tid)
        else:
            new_items.append({
                'id': tid, 'text': t.get('text', ''),
                'status': t.get('status', 'MISSING'),
            })

    for t in old_traces:
        if t['id'] not in matched_old:
            text = t.get('text', '').strip().lower()
            if text not in new_by_text:
                removed.append({
                    'id': t['id'], 'text': t.get('text', ''),
                    'status': t.get('status', 'MISSING'),
                })

    old_summary = old_map.get('summary', {})
    new_summary = new_map.get('summary', {})
    old_pct = old_summary.get('coverage_score_pct', 0)
    new_pct = new_summary.get('coverage_score_pct', 0)

    summary = {
        'old_coverage_pct': old_pct,
        'new_coverage_pct': new_pct,
        'coverage_diff': round(new_pct - old_pct, 1),
        'improved_count': len(improved),
        'regressed_count': len(regressed),
        'new_count': len(new_items),
        'removed_count': len(removed),
        'unchanged_count': len(unchanged),
    }

    if 'reverse_coverage_pct' in old_summary or 'reverse_coverage_pct' in new_summary:
        old_rev = old_summary.get('reverse_coverage_pct', 0)
        new_rev = new_summary.get('reverse_coverage_pct', 0)
        summary['old_reverse_pct'] = old_rev
        summary['new_reverse_pct'] = new_rev
        summary['reverse_diff'] = round(new_rev - old_rev, 1)

    return {
        'summary': summary,
        'improved': improved,
        'regressed': regressed,
        'new': new_items,
        'removed': removed,
    }


def format_text(delta: dict) -> str:
    s = delta['summary']
    lines = []

    diff_str = f"+{s['coverage_diff']}" if s['coverage_diff'] >= 0 else str(s['coverage_diff'])
    lines.append(f"Forward: {s['old_coverage_pct']}% → {s['new_coverage_pct']}% ({diff_str}%)")

    if 'old_reverse_pct' in s:
        rev_diff = f"+{s['reverse_diff']}" if s['reverse_diff'] >= 0 else str(s['reverse_diff'])
        lines.append(f"Reverse: {s['old_reverse_pct']}% → {s['new_reverse_pct']}% ({rev_diff}%)")

    lines.append('')

    if delta['improved']:
        lines.append(f"IMPROVED ({len(delta['improved'])}):")
        for item in delta['improved']:
            lines.append(f"  ▲ {item['id']}  {item['old_status']} → {item['new_status']}")
            lines.append(f"    {item['text']}")
        lines.append('')

    if delta['regressed']:
        lines.append(f"REGRESSED ({len(delta['regressed'])}):")
        for item in delta['regressed']:
            lines.append(f"  ▼ {item['id']}  {item['old_status']} → {item['new_status']}")
            lines.append(f"    {item['text']}")
        lines.append('')

    if delta['new']:
        lines.append(f"NEW ({len(delta['new'])}):")
        for item in delta['new']:
            lines.append(f"  + {item['id']}  [{item['status']}]")
            lines.append(f"    {item['text']}")
        lines.append('')

    if delta['removed']:
        lines.append(f"REMOVED ({len(delta['removed'])}):")
        for item in delta['removed']:
            lines.append(f"  - {item['id']}  [{item['status']}]")
            lines.append(f"    {item['text']}")
        lines.append('')

    if not any([delta['improved'], delta['regressed'], delta['new'], delta['removed']]):
        lines.append('No changes.')

    lines.append(f"Unchanged: {s['unchanged_count']} traces")

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: delta.py <old-trace-map.json> <new-trace-map.json> [--json]", file=sys.stderr)
        sys.exit(1)

    old_map = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    new_map = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
    use_json = '--json' in sys.argv

    delta = compare(old_map, new_map)

    if use_json:
        json.dump(delta, sys.stdout, ensure_ascii=False, indent=2)
    else:
        print(format_text(delta))


if __name__ == '__main__':
    main()
