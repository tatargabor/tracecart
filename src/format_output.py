#!/usr/bin/env python3
"""Format requirements JSON into markdown output documents.

Takes structured JSON (from LLM extraction) and produces:
- consolidated-requirements.md (requirements table)
- coverage-matrix.md (verification results)

All formatting is deterministic — no LLM needed.
"""

import json
import sys
from datetime import date
from pathlib import Path


DOMAIN_TAGS = [
    'orders', 'email', 'ai', 'inventory', 'manufacturing',
    'logistics', 'communication', 'crm', 'partners', 'billing',
    'products', 'sites', 'capacity', 'shipping', 'documents',
    'statistics', 'portal', 'pricing',
]

VALID_TYPES = ['REQUIREMENT', 'DECISION', 'WISH', 'OPEN_QUESTION', 'EXCLUSION']
COVERAGE_STATUSES = ['COVERED', 'PARTIAL', 'MISSING', 'DEFERRED', 'N/A']


def validate_tags(tags: list[str]) -> list[str]:
    """Validate domain tags against known list. Return unknown tags."""
    return [t for t in tags if t not in DOMAIN_TAGS]


def validate_requirement(req: dict) -> list[str]:
    """Validate a single requirement entry. Return list of issues."""
    issues = []

    if not req.get('id'):
        issues.append('missing id')
    if req.get('type') not in VALID_TYPES:
        issues.append(f'invalid type: {req.get("type")}')

    unknown_tags = validate_tags(req.get('tags', []))
    if unknown_tags:
        issues.append(f'unknown tags: {unknown_tags}')

    if not req.get('text'):
        issues.append('missing text')

    return issues


def format_consolidated(requirements: list[dict], sources: dict) -> str:
    """Format requirements as consolidated-requirements.md."""
    type_counts = {}
    tag_counts = {}
    issues = []

    for req in requirements:
        t = req.get('type', 'UNKNOWN')
        type_counts[t] = type_counts.get(t, 0) + 1

        for tag in req.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        req_issues = validate_requirement(req)
        if req_issues:
            issues.append(f'{req.get("id", "?")}: {", ".join(req_issues)}')

    unused_tags = [t for t in DOMAIN_TAGS if t not in tag_counts]

    lines = [
        '---',
        f'generated: "{date.today().isoformat()}"',
        'method: "extract-adversarial-verify (Method C)"',
        f'total_requirements: {len(requirements)}',
        f'by_type: {json.dumps(type_counts)}',
        '---',
        '',
        '# Konszolidált Követelmények',
        '',
        '## Summary',
        '',
        f'- **Total:** {len(requirements)} requirements',
        f'- **Types:** {", ".join(f"{v} {k}" for k, v in sorted(type_counts.items()))}',
        f'- **Sources:** {sources.get("baseline", "?")}' + (f' + {sources.get("overlays", 0)} overlays' if sources.get('overlays') else ''),
        '',
    ]

    if unused_tags:
        lines.append(f'> **Warning:** No requirements tagged with: {", ".join(unused_tags)}')
        lines.append('')

    if issues:
        lines.append('> **Validation issues:**')
        for issue in issues:
            lines.append(f'>   - {issue}')
        lines.append('')

    lines.extend([
        '## Requirements',
        '',
        '| ID | Type | Tags | Text | Source |',
        '|----|------|------|------|--------|',
    ])

    for req in sorted(requirements, key=lambda r: r.get('id', '')):
        req_id = req.get('id', '?')
        req_type = req.get('type', '?')
        tags = ', '.join(req.get('tags', []))
        text = req.get('text', '').replace('|', '\\|').replace('\n', ' ')
        source = req.get('source_section', req.get('source', '—'))
        history = req.get('history', '')

        if history:
            text += f' *(módosítva: {history})*'

        lines.append(f'| {req_id} | {req_type} | {tags} | {text} | {source} |')

    lines.append('')
    return '\n'.join(lines)


def format_coverage(requirements: list[dict], coverage: list[dict], reverse: list[dict] = None) -> str:
    """Format coverage verification as coverage-matrix.md."""
    status_counts = {}
    for item in coverage:
        s = item.get('status', 'UNKNOWN')
        status_counts[s] = status_counts.get(s, 0) + 1

    total_checkable = sum(v for k, v in status_counts.items() if k != 'N/A')
    covered = status_counts.get('COVERED', 0) + status_counts.get('PARTIAL', 0)
    score = (covered / total_checkable * 100) if total_checkable > 0 else 0

    lines = [
        '---',
        f'generated: "{date.today().isoformat()}"',
        'method: "bidirectional-trace"',
        f'coverage_score: {score:.1f}%',
        '---',
        '',
        '# Lefedettség Mátrix',
        '',
        '## Forward (Követelmények → Specifikáció)',
        '',
        f'**Coverage score: {score:.1f}%** (COVERED + PARTIAL / checkable)',
        '',
        '| Státusz | Darab | % |',
        '|---------|-------|---|',
    ]

    total = len(coverage)
    for status in COVERAGE_STATUSES:
        count = status_counts.get(status, 0)
        pct = (count / total * 100) if total > 0 else 0
        lines.append(f'| {status} | {count} | {pct:.0f}% |')

    missing = [c for c in coverage if c.get('status') == 'MISSING']
    if missing:
        lines.extend([
            '',
            '## Kritikus hiányok (MISSING)',
            '',
            '| ID | Requirement | Notes |',
            '|----|-------------|-------|',
        ])
        for item in missing:
            req = next((r for r in requirements if r.get('id') == item.get('id')), {})
            lines.append(f'| {item.get("id", "?")} | {req.get("text", "?").replace("|", "\\|")} | {item.get("notes", "—")} |')

    partial = [c for c in coverage if c.get('status') == 'PARTIAL']
    if partial:
        lines.extend([
            '',
            '## Részleges lefedettség (PARTIAL)',
            '',
            '| ID | Spec ref | Mi hiányzik |',
            '|----|----------|-------------|',
        ])
        for item in partial:
            lines.append(f'| {item.get("id", "?")} | {item.get("spec_ref", "—")} | {item.get("notes", "—")} |')

    if reverse:
        untraced = [r for r in reverse if r.get('status') == 'UNTRACED']
        if untraced:
            lines.extend([
                '',
                '## Scope creep (UNTRACED spec content)',
                '',
                '| Spec | Section | Summary | Notes |',
                '|------|---------|---------|-------|',
            ])
            for item in untraced:
                lines.append(f'| {item.get("spec_file", "?")} | {item.get("section", "?")} | {item.get("summary", "?")} | {item.get("notes", "—")} |')

    deferred = [c for c in coverage if c.get('status') == 'DEFERRED']
    if deferred:
        lines.extend([
            '',
            '## Deferred (M2+)',
            '',
            '| ID | Requirement |',
            '|----|-------------|',
        ])
        for item in deferred:
            req = next((r for r in requirements if r.get('id') == item.get('id')), {})
            lines.append(f'| {item.get("id", "?")} | {req.get("text", "?").replace("|", "\\|")} |')

    lines.extend([
        '',
        '## Teljes forward mátrix',
        '',
        '| ID | Type | Status | Spec ref | Notes |',
        '|----|------|--------|----------|-------|',
    ])

    for item in sorted(coverage, key=lambda c: c.get('id', '')):
        req = next((r for r in requirements if r.get('id') == item.get('id')), {})
        lines.append(f'| {item.get("id", "?")} | {req.get("type", "?")} | {item.get("status", "?")} | {item.get("spec_ref", "—")} | {item.get("notes", "—").replace("|", "\\|")} |')

    lines.append('')
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: format_output.py <mode> <input.json> [output.md]", file=sys.stderr)
        print("  mode: consolidated | coverage", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]
    input_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    data = json.loads(input_path.read_text(encoding='utf-8'))

    if mode == 'consolidated':
        result = format_consolidated(
            data.get('requirements', data if isinstance(data, list) else []),
            data.get('sources', {}),
        )
    elif mode == 'coverage':
        result = format_coverage(
            data.get('requirements', []),
            data.get('coverage', []),
            data.get('reverse', []),
        )
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)

    if output_path:
        output_path.write_text(result, encoding='utf-8')
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        print(result)


if __name__ == '__main__':
    main()
