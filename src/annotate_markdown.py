#!/usr/bin/env python3
"""Generate annotated markdown from extraction + coverage results.

Reads:
- Original source text
- Extraction JSON (sentences per line)
- Coverage JSON (status per sentence)
- Override map (optional, for SUPERSEDED/CONFLICT markers)

Outputs:
- Annotated markdown with Obsidian callout blocks after each source line
- YAML frontmatter with coverage summary
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


CALLOUT_MAP = {
    'COVERED': ('trace-covered', '✅'),
    'PARTIAL': ('trace-partial', '⚠️'),
    'MISSING': ('trace-missing', '⬜'),
    'DEFERRED': ('trace-deferred', '⏭️'),
    'N/A': ('trace-na', '💬'),
    'SUPERSEDED': ('trace-superseded', '➡️'),
    'CONFLICT': ('trace-conflict', '⚡'),
}


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def build_line_map(extraction: dict, coverage: dict, overrides: dict = None) -> dict:
    """Build a map: line_number → list of annotated sentences."""
    sentences = extraction.get('sentences', [])
    coverage_results = {r['sentence_id']: r for r in coverage.get('results', [])}
    status_map = overrides.get('status_map', {}) if overrides else {}

    line_map = defaultdict(list)

    for sent in sentences:
        sid = sent['id']
        line_num = sent.get('source_line', sent.get('line_number', 0))

        override_status = status_map.get(sid)
        if override_status == 'SUPERSEDED':
            status = 'SUPERSEDED'
            spec_ref = ''
            notes = f"Superseded by {overrides.get('overrides', [{}])[0].get('superseded_by', '?')}"
        elif override_status == 'CONFLICT':
            status = 'CONFLICT'
            spec_ref = ''
            notes = 'Conflict detected — see override map'
        elif sid in coverage_results:
            cr = coverage_results[sid]
            status = cr.get('status', 'MISSING')
            spec_ref = cr.get('spec_ref', '')
            notes = cr.get('notes', '')
        else:
            status = 'MISSING'
            spec_ref = ''
            notes = 'Not verified'

        callout_type, emoji = CALLOUT_MAP.get(status, ('trace-missing', '⬜'))

        line_map[line_num].append({
            'id': sid,
            'text': sent.get('text', ''),
            'status': status,
            'callout_type': callout_type,
            'emoji': emoji,
            'spec_ref': spec_ref,
            'notes': notes,
            'implicit': sent.get('implicit', False),
            'type': sent.get('type', 'REQUIREMENT'),
        })

    return dict(line_map)


def compute_summary(line_map: dict) -> dict:
    """Compute coverage summary from line map."""
    counts = defaultdict(int)
    total = 0
    for annotations in line_map.values():
        for ann in annotations:
            counts[ann['status']] += 1
            total += 1

    return {
        'total': total,
        'covered': counts.get('COVERED', 0),
        'partial': counts.get('PARTIAL', 0),
        'missing': counts.get('MISSING', 0),
        'deferred': counts.get('DEFERRED', 0),
        'na': counts.get('N/A', 0),
        'superseded': counts.get('SUPERSEDED', 0),
        'conflict': counts.get('CONFLICT', 0),
    }


def generate_annotated_markdown(
    source_text: str,
    line_map: dict,
    summary: dict,
    metadata: dict,
) -> str:
    """Generate the annotated markdown output."""
    lines = source_text.split('\n')

    parts = []

    parts.append('---')
    parts.append(f'generated: "{metadata.get("generated", "")}"')
    parts.append(f'source: "{metadata.get("source", "")}"')
    if metadata.get('chapter'):
        parts.append(f'chapter: {metadata["chapter"]}')
    parts.append(f'coverage: {{covered: {summary["covered"]}, partial: {summary["partial"]}, missing: {summary["missing"]}, deferred: {summary["deferred"]}, superseded: {summary["superseded"]}}}')

    score_denom = summary['covered'] + summary['partial'] + summary['missing']
    if score_denom > 0:
        score = (summary['covered'] + summary['partial']) / score_denom * 100
        parts.append(f'coverage_score: "{score:.0f}%"')

    parts.append('---')
    parts.append('')

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1
        parts.append(line)

        if line_num in line_map:
            annotations = line_map[line_num]

            grouped = defaultdict(list)
            for ann in annotations:
                grouped[ann['callout_type']].append(ann)

            for callout_type, anns in grouped.items():
                parts.append('')
                parts.append(f'> [!{callout_type}]')
                for ann in anns:
                    ref_part = f' — *{ann["spec_ref"]}*' if ann['spec_ref'] else ''
                    notes_part = f' — {ann["notes"]}' if ann['notes'] and ann['status'] in ('PARTIAL', 'MISSING', 'CONFLICT', 'SUPERSEDED') else ''
                    implicit_mark = ' *(implicit)*' if ann['implicit'] else ''
                    parts.append(f'> {ann["emoji"]} `{ann["id"]}` {ann["text"][:120]}{implicit_mark}{ref_part}{notes_part}')

                parts.append('')

    return '\n'.join(parts)


def generate_summary_md(all_summaries: list[dict]) -> str:
    """Generate top-level summary.md dashboard."""
    parts = ['# Traceability Summary', '']

    total_all = sum(s['summary']['total'] for s in all_summaries)
    covered_all = sum(s['summary']['covered'] for s in all_summaries)
    partial_all = sum(s['summary']['partial'] for s in all_summaries)
    missing_all = sum(s['summary']['missing'] for s in all_summaries)

    denom = covered_all + partial_all + missing_all
    score = (covered_all + partial_all) / denom * 100 if denom > 0 else 0

    parts.append(f'**Overall coverage: {score:.0f}%** ({covered_all} covered + {partial_all} partial / {denom} checkable)')
    parts.append('')
    parts.append('## Coverage by Input')
    parts.append('')
    parts.append('| Input | Sentences | ✅ Covered | ⚠️ Partial | ⬜ Missing | ➡️ Superseded | Score |')
    parts.append('|-------|-----------|-----------|-----------|----------|-------------|-------|')

    for entry in all_summaries:
        s = entry['summary']
        d = s['covered'] + s['partial'] + s['missing']
        sc = (s['covered'] + s['partial']) / d * 100 if d > 0 else 0
        name = entry.get('name', entry.get('source', '?'))
        parts.append(f'| {name} | {s["total"]} | {s["covered"]} | {s["partial"]} | {s["missing"]} | {s["superseded"]} | {sc:.0f}% |')

    missing_items = []
    for entry in all_summaries:
        for ann_list in entry.get('line_map', {}).values():
            for ann in ann_list:
                if ann['status'] == 'MISSING':
                    missing_items.append(ann)

    if missing_items:
        parts.extend(['', '## Top Gaps (MISSING)', ''])
        parts.append('| ID | Text | Type |')
        parts.append('|----|------|------|')
        for item in missing_items[:20]:
            parts.append(f'| `{item["id"]}` | {item["text"][:80]} | {item["type"]} |')

    parts.append('')
    return '\n'.join(parts)


def main():
    if len(sys.argv) < 4:
        print("Usage: annotate_markdown.py <source_text> <extraction.json> <coverage.json> [overrides.json] [output.md]", file=sys.stderr)
        sys.exit(1)

    source_path = Path(sys.argv[1])
    extraction_path = Path(sys.argv[2])
    coverage_path = Path(sys.argv[3])
    overrides_path = Path(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != '-' else None
    output_path = Path(sys.argv[5]) if len(sys.argv) > 5 else None

    source_text = source_path.read_text(encoding='utf-8')
    extraction = load_json(str(extraction_path))
    coverage = load_json(str(coverage_path))
    overrides = load_json(str(overrides_path)) if overrides_path and overrides_path.exists() else {}

    from datetime import date
    line_map = build_line_map(extraction, coverage, overrides)
    summary = compute_summary(line_map)

    metadata = {
        'generated': date.today().isoformat(),
        'source': str(source_path),
        'chapter': extraction.get('chapter'),
    }

    result = generate_annotated_markdown(source_text, line_map, summary, metadata)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding='utf-8')
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        print(result)


if __name__ == '__main__':
    main()
