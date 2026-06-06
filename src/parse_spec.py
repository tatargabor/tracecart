#!/usr/bin/env python3
"""Parse a specification document into chapters.

Detects chapter boundaries, extracts text per chapter,
and outputs structured JSON for downstream processing.

Handles the WPC spec format where chapters appear twice:
once in the TOC (short references) and once as full content.
We use the LAST occurrence of each chapter number as the content start.
"""

import json
import re
import sys
from pathlib import Path


def find_chapter_boundaries(lines: list[str]) -> list[dict]:
    """Find chapter start lines from the MAIN content block.

    The WPC spec has 3 blocks with chapter numbering:
    1. TOC (consecutive headers, no content between — skip)
    2. Main content (full chapters with content — USE THIS)
    3. Condensed summary (shorter, restarts numbering — skip)

    Strategy: find all chapter-header lines, group into blocks.
    A block is "TOC-like" if chapters are dense (< 3 lines apart on average).
    The first non-TOC block is the main content.
    """
    pattern = re.compile(r'^(\d+)\\?\.\s+(.+)$')

    all_headers = []
    for i, line in enumerate(lines):
        m = pattern.match(line.strip())
        if m:
            all_headers.append({
                'number': int(m.group(1)),
                'title': m.group(2).strip(),
                'line': i,
            })

    if not all_headers:
        return []

    blocks = []
    current_block = [all_headers[0]]

    for h in all_headers[1:]:
        prev = current_block[-1]
        if h['number'] <= 1 and prev['number'] > 5:
            blocks.append(current_block)
            current_block = [h]
        else:
            current_block.append(h)

    blocks.append(current_block)

    main_block = None
    for block in blocks:
        if len(block) < 3:
            continue
        avg_gap = (block[-1]['line'] - block[0]['line']) / len(block)
        if avg_gap > 10:
            main_block = block
            break

    if main_block is None:
        main_block = max(blocks, key=lambda b: b[-1]['line'] - b[0]['line'])

    chapters = []
    for i, h in enumerate(main_block):
        end_line = main_block[i + 1]['line'] if i + 1 < len(main_block) else len(lines)
        if i + 1 < len(main_block):
            end_line = main_block[i + 1]['line']
        else:
            for block in blocks:
                if block[0]['line'] > h['line'] and block is not main_block:
                    end_line = block[0]['line']
                    break

        chapters.append({
            'number': h['number'],
            'title': h['title'],
            'start_line': h['line'],
            'end_line': end_line,
        })

    return chapters


def extract_chapter_text(lines: list[str], chapter: dict) -> str:
    """Extract the text content for a chapter."""
    start = chapter['start_line']
    end = chapter['end_line']
    return '\n'.join(line for line in lines[start:end])


def count_content_lines(text: str) -> int:
    """Count non-empty, non-header lines (actual content)."""
    count = 0
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not re.match(r'^\d+\.\d+', stripped):
            count += 1
    return count


def parse_sections(text: str, chapter_num: int) -> list[dict]:
    """Parse sub-sections within a chapter."""
    pattern = re.compile(rf'^{chapter_num}\.(\d+)\s+(.+)$')
    sections = []

    for line in text.split('\n'):
        m = pattern.match(line.strip())
        if m:
            sections.append({
                'number': f'{chapter_num}.{m.group(1)}',
                'title': m.group(2).strip(),
            })

    return sections


def main():
    if len(sys.argv) < 2:
        print("Usage: parse_spec.py <spec_file> [chapter_number]", file=sys.stderr)
        sys.exit(1)

    spec_path = Path(sys.argv[1])
    target_chapter = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not spec_path.exists():
        print(f"Error: {spec_path} not found", file=sys.stderr)
        sys.exit(1)

    lines = spec_path.read_text(encoding='utf-8').split('\n')
    chapters = find_chapter_boundaries(lines)

    if target_chapter is not None:
        chapters = [c for c in chapters if c['number'] == target_chapter]
        if not chapters:
            print(f"Error: chapter {target_chapter} not found", file=sys.stderr)
            sys.exit(1)

    result = []
    for ch in chapters:
        text = extract_chapter_text(lines, ch)
        sections = parse_sections(text, ch['number'])
        content_lines = count_content_lines(text)

        result.append({
            'number': ch['number'],
            'title': ch['title'],
            'start_line': ch['start_line'] + 1,
            'end_line': ch['end_line'],
            'sections': sections,
            'content_lines': content_lines,
            'text': text,
        })

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
