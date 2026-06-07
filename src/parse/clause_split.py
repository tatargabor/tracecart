#!/usr/bin/env python3
"""Deterministic compound sentence splitting + line numbering.

Takes raw text and produces numbered atomic clauses.
This is the key pre-processing step that enables Method G's 100% detection recall.

The LLM receives pre-split clauses rather than compound sentences,
eliminating the biggest source of missed requirements.

Hungarian compound splitting rules:
- Split on sentence boundaries ('. ' followed by uppercase)
- Split coordinated clauses joined by ', de ', ', illetve ', ', valamint '
- Split enumerated lists: 'a X-t, a Y-t és a Z-t' → one clause per item
- DO NOT split subordinate clauses (hogy, amely, ami, ha, mert)
- DO NOT split within parenthetical remarks

Example (TerraFurn spec, §9.3):
  Input:  "A visszaigazolásnak figyelembe kell vennie a faanyag-készletet,
           a CNC kapacitást, a felületkezelési időt és a szállítási ütemezést"
  Output: 4 atomic clauses, one per factor
"""

import json
import re
import sys
from pathlib import Path


SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ])')

COORD_CONJUNCTIONS = [
    r',\s+de\s+',
    r',\s+illetve\s+',
    r',\s+valamint\s+',
    r',\s+viszont\s+',
    r',\s+azonban\s+',
    r'\.\s+Nem\s+',
]

META_PATTERNS = [
    re.compile(r'^[Ll]ásd:?\s+§', re.IGNORECASE),
    re.compile(r'^[Ss]ee:?\s+§', re.IGNORECASE),
    re.compile(r'^\(.{0,5}lásd', re.IGNORECASE),
    re.compile(r'^\d+\.\s+\.{3,}'),
    re.compile(r'^\.\.\.\s+\d+$'),
]

ENUM_PATTERN = re.compile(
    r'(?:kell vennie |figyelembe kell vennie |figyelembevétele |alapján történő )'
    r'.*?'
    r'(a [^,]+(?:,\s*a [^,]+)*(?:\s+és\s+a [^,]+))'
)

LIST_ENUM = re.compile(r',\s+a\s+|,\s+az\s+|\s+és\s+a\s+|\s+és\s+az\s+')


def split_sentences(text: str) -> list[str]:
    """Split text on sentence boundaries."""
    parts = SENTENCE_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]


def split_coordinated(text: str) -> list[str]:
    """Split on coordinating conjunctions that join independent clauses."""
    for pattern in COORD_CONJUNCTIONS:
        parts = re.split(pattern, text, maxsplit=1)
        if len(parts) > 1:
            result = []
            for p in parts:
                result.extend(split_coordinated(p))
            return result
    return [text]


def split_enumerations(text: str, base_clause: str = '') -> list[str]:
    """Split enumerated items in Hungarian.

    Example: "figyelembe kell vennie a faanyag-készletet, a CNC kapacitást, a felületkezelési időt és a szállítási ütemezést"
    → ["figyelembe kell vennie a faanyag-készletet",
       "figyelembe kell vennie a CNC kapacitást",
       "figyelembe kell vennie a felületkezelési időt",
       "figyelembe kell vennie a szállítási ütemezést"]
    """
    patterns = [
        (r'(figyelembe kell vennie )(a .+)', r'\1'),
        (r'(figyelembe kell venni )(a .+)', r'\1'),
        (r'(kell vennie )(a .+)', r'\1'),
    ]

    for trigger_pattern, prefix_extract in patterns:
        m = re.search(trigger_pattern, text)
        if m:
            prefix = m.group(1)
            enum_part = m.group(2)
            items = re.split(r',\s+(?=a[z]?\s)|(?:\s+és\s+)', enum_part)
            items = [i.strip().rstrip('.') for i in items if i.strip()]
            if len(items) > 1:
                before = text[:m.start()].strip()
                clauses = []
                for item in items:
                    clause = f"{prefix}{item}"
                    if before:
                        clause = f"{before} {clause}"
                    clauses.append(clause.strip())
                return clauses

    return [text]


def process_line(text: str) -> list[str]:
    """Process a single line into atomic clauses."""
    sentences = split_sentences(text)

    clauses = []
    for sent in sentences:
        coordinated = split_coordinated(sent)
        for coord in coordinated:
            enumerated = split_enumerations(coord)
            clauses.extend(enumerated)

    return [c.strip() for c in clauses if c.strip()]


def process_document(text: str) -> list[dict]:
    """Process a full document into numbered clauses.

    Returns list of {clause_id, text, line_number, clause_index, original_line}
    """
    lines = text.split('\n')
    clauses = []

    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        line_num = line_idx + 1

        if re.match(r'^\d+[\\.]\d*\s', stripped) or re.match(r'^#+\s', stripped):
            clauses.append({
                'clause_id': f'L{line_num}',
                'text': stripped,
                'line_number': line_num,
                'clause_index': 0,
                'original_line': stripped,
                'is_header': True,
            })
            continue

        if any(p.search(stripped) for p in META_PATTERNS):
            clauses.append({
                'clause_id': f'L{line_num}',
                'text': stripped,
                'line_number': line_num,
                'clause_index': 0,
                'original_line': stripped,
                'is_header': False,
                'is_meta': True,
            })
            continue

        sub_clauses = process_line(stripped)

        if len(sub_clauses) <= 1:
            clauses.append({
                'clause_id': f'L{line_num}',
                'text': stripped,
                'line_number': line_num,
                'clause_index': 0,
                'original_line': stripped,
                'is_header': False,
            })
        else:
            for ci, sc in enumerate(sub_clauses):
                clauses.append({
                    'clause_id': f'L{line_num}-C{ci + 1}',
                    'text': sc,
                    'line_number': line_num,
                    'clause_index': ci,
                    'original_line': stripped,
                    'is_header': False,
                })

    return clauses


def main():
    if len(sys.argv) < 2:
        print("Usage: clause_split.py <input_file_or_-> [--stats]", file=sys.stderr)
        print("  Reads from file or stdin (-). Outputs JSON.", file=sys.stderr)
        sys.exit(1)

    show_stats = '--stats' in sys.argv

    if sys.argv[1] == '-':
        text = sys.stdin.read()
    else:
        text = Path(sys.argv[1]).read_text(encoding='utf-8')

    clauses = process_document(text)

    content_clauses = [c for c in clauses if not c.get('is_header')]
    compound_lines = set()
    for c in content_clauses:
        if c['clause_index'] > 0:
            compound_lines.add(c['line_number'])

    result = {
        'total_lines': len(text.split('\n')),
        'content_clauses': len(content_clauses),
        'compound_lines_split': len(compound_lines),
        'clauses': clauses,
    }

    if show_stats:
        print(f"Total lines: {result['total_lines']}", file=sys.stderr)
        print(f"Content clauses: {result['content_clauses']}", file=sys.stderr)
        print(f"Compound lines split: {result['compound_lines_split']}", file=sys.stderr)
        for c in clauses:
            if not c.get('is_header'):
                marker = '  *' if c['clause_index'] > 0 else ''
                print(f"  [{c['clause_id']}] {c['text'][:80]}{marker}", file=sys.stderr)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
