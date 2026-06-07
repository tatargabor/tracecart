#!/usr/bin/env python3
"""Discover and sort all input documents chronologically.

Scans docs/converted/ for meetings and emails, extracts dates
from filenames, and returns a sorted list for processing.

Skips non-content files (test emails, calendar invites, happening-now notifications).
"""

import json
import re
import sys
from pathlib import Path

SKIP_PATTERNS = [
    r'teszt-',
    r'calendar-invite-',
    r'happening-now-',
    r'invitation-for-',
]

DATE_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2})')


def extract_date(filename: str) -> str | None:
    """Extract YYYY-MM-DD date from filename."""
    m = DATE_PATTERN.search(filename)
    return m.group(1) if m else None


def should_skip(filename: str) -> bool:
    """Check if file should be skipped based on filename patterns."""
    lower = filename.lower()
    return any(re.search(p, lower) for p in SKIP_PATTERNS)


def classify_document(path: Path) -> str:
    """Classify document type from its path."""
    parts = path.parts
    if 'meetings' in parts:
        return 'meeting'
    if 'emails' in parts:
        return 'email'
    if 'discord' in parts:
        return 'discord'
    if 'discord-voice' in parts:
        return 'discord-voice'
    if 'client-spec' in parts:
        return 'client-spec'
    return 'other'


def discover(base_dir: Path) -> list[dict]:
    """Find all input documents and sort chronologically."""
    results = []

    converted_dir = base_dir / 'docs' / 'converted'
    if not converted_dir.exists():
        print(f"Error: {converted_dir} not found", file=sys.stderr)
        sys.exit(1)

    for md_file in sorted(converted_dir.rglob('*.md')):
        filename = md_file.name

        if should_skip(filename):
            continue

        doc_type = classify_document(md_file)
        date = extract_date(filename)
        rel_path = str(md_file.relative_to(base_dir))

        results.append({
            'path': rel_path,
            'filename': filename,
            'type': doc_type,
            'date': date or '0000-00-00',
        })

    results.sort(key=lambda d: (d['date'], d['path']))

    return results


def main():
    base_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    documents = discover(base_dir)

    summary = {}
    for doc in documents:
        t = doc['type']
        summary[t] = summary.get(t, 0) + 1

    output = {
        'base_dir': str(base_dir),
        'total': len(documents),
        'by_type': summary,
        'documents': documents,
    }

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
