#!/usr/bin/env python3
"""Trace extraction orchestration module.

Reads clauses JSON (from clause_split.py), formats the extraction prompt,
and validates the LLM subagent response. This module handles the data
transformation around the LLM call — the actual LLM call is made by
the Claude Code agent that invokes this script.

Two modes:
1. format-prompt: clauses.json → prompt text (agent sends to subagent)
2. validate: raw LLM output → validated traces JSON (agent saves result)

The agent orchestrates: format-prompt → subagent call → validate → remainder check.
"""

import hashlib
import json
import sys
from pathlib import Path

VALID_TYPES = {'REQUIREMENT', 'DECISION', 'WISH', 'OPEN_QUESTION', 'EXCLUSION'}

PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent.parent / 'prompts'


def format_prompt(clauses: list[dict], source_file: str = '', language: str = 'hu') -> str:
    """Format extraction prompt from clauses.

    Args:
        clauses: list of clause dicts from clause_split
        source_file: source file path for context
        language: 'hu' for Hungarian prompts, 'en' for English
    """
    if language == 'en':
        template_path = PROMPT_TEMPLATE_PATH / 'en' / 'extract.txt'
    else:
        template_path = PROMPT_TEMPLATE_PATH / 'extract.txt'

    template = template_path.read_text(encoding='utf-8')

    clause_lines = []
    for c in clauses:
        if c.get('is_header') or c.get('is_meta'):
            continue
        clause_lines.append(f"[{c['clause_id']}] {c['text']}")

    clauses_text = '\n'.join(clause_lines)
    return template.replace('{clauses}', clauses_text)


def source_hash(filepath: str) -> str:
    """Compute 6-char hash from file path for trace IDs."""
    return hashlib.sha256(filepath.encode('utf-8')).hexdigest()[:6]


def validate_traces(raw_output: str, clauses: list[dict], source_file: str = '', id_prefix: str = 'T') -> dict:
    """Validate and normalize LLM extraction output.

    Args:
        raw_output: raw text from LLM subagent (should be JSON array)
        clauses: original clauses for cross-referencing
        source_file: source file path for generating trace IDs
        id_prefix: ID prefix ('T' for forward, 'RT' for reverse)

    Returns:
        dict with 'traces' (valid traces) and 'errors' (validation issues)
    """
    errors = []
    traces = []

    parsed = _parse_json_output(raw_output)
    if parsed is None:
        return {'traces': [], 'errors': ['Failed to parse LLM output as JSON']}

    if not isinstance(parsed, list):
        return {'traces': [], 'errors': ['LLM output is not a JSON array']}

    clause_map = {c['clause_id']: c for c in clauses if not c.get('is_header') and not c.get('is_meta')}
    file_hash = source_hash(source_file)
    id_counter = {}

    for i, entry in enumerate(parsed):
        if not isinstance(entry, dict):
            errors.append(f'Entry {i}: not a dict')
            continue

        clause_id = entry.get('clause_id')
        if not clause_id:
            clause_ids = entry.get('clause_ids', [])
            if clause_ids:
                clause_id = clause_ids[0]
            else:
                errors.append(f'Entry {i}: missing clause_id')
                continue

        trace_type = entry.get('type', '').upper()
        if trace_type not in VALID_TYPES:
            errors.append(f'Entry {i}: invalid type "{trace_type}"')
            trace_type = 'REQUIREMENT'

        text = entry.get('text', '')
        if not text:
            errors.append(f'Entry {i}: missing text')
            continue

        clause = clause_map.get(clause_id)
        line_num = clause['line_number'] if clause else 0
        clause_idx = clause['clause_index'] if clause else 0

        base_id = f'{id_prefix}-{file_hash}-{line_num:03d}-{clause_idx}'
        seq = id_counter.get(base_id, 0)
        id_counter[base_id] = seq + 1
        trace_id = base_id if seq == 0 else f'{base_id}-{seq}'

        trace = {
            'id': trace_id,
            'text': text,
            'type': trace_type,
            'source': {
                'file': source_file,
                'line': line_num,
                'col_start': 0,
                'col_end': len(clause['text']) if clause else len(text),
            },
            'clause_id': clause_id,
            'clause_ids': entry.get('clause_ids', [clause_id]),
            'topics': entry.get('tags', entry.get('topics', [])),
            'implicit': entry.get('implicit', False),
            'triple': entry.get('triple'),
        }

        if entry.get('signal'):
            trace['signal'] = entry['signal']

        traces.append(trace)

    return {'traces': traces, 'errors': errors}


def _parse_json_output(raw: str) -> list | None:
    """Parse JSON from LLM output, handling common issues."""
    raw = raw.strip()

    if raw.startswith('```json'):
        raw = raw[7:]
    if raw.startswith('```'):
        raw = raw[3:]
    if raw.endswith('```'):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find('[')
    end = raw.rfind(']')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def merge_traces(existing: list[dict], new_traces: list[dict]) -> list[dict]:
    """Merge new traces into existing, avoiding duplicates by clause_id coverage."""
    existing_clause_ids = set()
    for t in existing:
        existing_clause_ids.add(t.get('clause_id', ''))
        existing_clause_ids.update(t.get('clause_ids', []))

    merged = list(existing)
    for t in new_traces:
        t_ids = set(t.get('clause_ids', [t.get('clause_id', '')]))
        if not t_ids.issubset(existing_clause_ids):
            merged.append(t)
            existing_clause_ids.update(t_ids)

    return merged


def main():
    if len(sys.argv) < 3:
        print("Usage: extract.py <mode> <args...>", file=sys.stderr)
        print("Modes:", file=sys.stderr)
        print("  format-prompt <clauses.json> [--lang hu|en] [--source <file>]", file=sys.stderr)
        print("  validate <raw_output.txt> <clauses.json> [--source <file>]", file=sys.stderr)
        print("  merge <existing_traces.json> <new_traces.json>", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == 'format-prompt':
        clauses_data = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
        clauses = clauses_data.get('clauses', clauses_data) if isinstance(clauses_data, dict) else clauses_data

        lang = 'hu'
        source_file = ''
        args = sys.argv[3:]
        for i, arg in enumerate(args):
            if arg == '--lang' and i + 1 < len(args):
                lang = args[i + 1]
            elif arg == '--source' and i + 1 < len(args):
                source_file = args[i + 1]

        prompt = format_prompt(clauses, source_file, lang)
        print(prompt)

    elif mode == 'validate':
        raw_output = Path(sys.argv[2]).read_text(encoding='utf-8')
        clauses_data = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
        clauses = clauses_data.get('clauses', clauses_data) if isinstance(clauses_data, dict) else clauses_data

        source_file = ''
        args = sys.argv[4:]
        for i, arg in enumerate(args):
            if arg == '--source' and i + 1 < len(args):
                source_file = args[i + 1]

        result = validate_traces(raw_output, clauses, source_file)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)

    elif mode == 'merge':
        existing = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
        new = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))

        if isinstance(existing, dict) and 'traces' in existing:
            existing = existing['traces']
        if isinstance(new, dict) and 'traces' in new:
            new = new['traces']

        merged = merge_traces(existing, new)
        json.dump({'traces': merged}, sys.stdout, ensure_ascii=False, indent=2)

    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
