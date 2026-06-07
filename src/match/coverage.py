#!/usr/bin/env python3
"""Coverage matching module.

Reads extracted traces and a target document, formats the coverage_check
prompt for LLM subagent matching, and validates the response.

Two modes:
1. format-prompt: traces.json + target.md → prompt text
2. validate: raw LLM output → validated coverage statuses
3. apply: merge coverage statuses back into traces

The agent orchestrates: format-prompt → subagent call → validate → apply.
"""

import json
import re
import sys
from pathlib import Path

VALID_STATUSES = {'COVERED', 'PARTIAL', 'MISSING', 'DEFERRED', 'N/A'}
VALID_REVERSE_STATUSES = {'TRACED', 'PARTIAL_SOURCE', 'UNTRACED_IN_SOURCE'}

PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent.parent / 'prompts'

MAX_TRACES_PER_BATCH = 20


def parse_target_sections(target_text: str, target_file: str = '') -> list[dict]:
    """Parse a target document into sections for matching."""
    sections = []
    current_section = None
    current_lines = []

    for i, line in enumerate(target_text.split('\n')):
        header_match = re.match(r'^(#{1,4})\s+(.+)$', line.strip())
        if not header_match:
            section_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', line.strip())
            if section_match:
                header_match = section_match

        if header_match:
            if current_section:
                current_section['text'] = '\n'.join(current_lines).strip()
                if current_section['text']:
                    sections.append(current_section)

            title = header_match.group(2) if hasattr(header_match, 'group') else line.strip()
            section_id = header_match.group(1) if header_match else ''
            if section_id.startswith('#'):
                section_id = f'§{len(section_id)}'

            current_section = {
                'id': section_id,
                'title': title,
                'file': target_file,
                'line': i + 1,
                'text': '',
            }
            current_lines = [line]
        elif current_section:
            current_lines.append(line)
        elif line.strip():
            if not current_section:
                current_section = {
                    'id': '§0',
                    'title': '(preamble)',
                    'file': target_file,
                    'line': 1,
                    'text': '',
                }
                current_lines = []
            current_lines.append(line)

    if current_section:
        current_section['text'] = '\n'.join(current_lines).strip()
        if current_section['text']:
            sections.append(current_section)

    return sections


def format_prompt(
    traces: list[dict],
    target_text: str,
    exclusions: str = '',
    language: str = 'hu',
) -> str:
    """Format coverage check prompt.

    Args:
        traces: extracted traces to check
        target_text: full target document text
        exclusions: scope exclusions text (for DEFERRED detection)
        language: 'hu' or 'en'
    """
    if language == 'en':
        template_path = PROMPT_TEMPLATE_PATH / 'en' / 'coverage_check.txt'
    else:
        template_path = PROMPT_TEMPLATE_PATH / 'coverage_check.txt'

    template = template_path.read_text(encoding='utf-8')

    req_lines = []
    for t in traces:
        tid = t.get('id', t.get('sentence_id', ''))
        text = t.get('text', '')
        ttype = t.get('type', 'REQUIREMENT')
        implicit = ' [implicit]' if t.get('implicit') else ''
        req_lines.append(f"[{tid}] ({ttype}{implicit}) {text}")

    prompt = template.replace('{requirements}', '\n'.join(req_lines))
    prompt = prompt.replace('{specs}', target_text)
    prompt = prompt.replace('{exclusions}', exclusions or '(none specified)')

    return prompt


def batch_traces(traces: list[dict], batch_size: int = MAX_TRACES_PER_BATCH) -> list[list[dict]]:
    """Split traces into batches for separate subagent calls."""
    return [traces[i:i + batch_size] for i in range(0, len(traces), batch_size)]


def validate_matches(raw_output: str, traces: list[dict]) -> dict:
    """Validate and normalize LLM matching output.

    Returns:
        dict with 'matches' (valid match results) and 'errors'
    """
    errors = []
    matches = []

    parsed = _parse_json_output(raw_output)
    if parsed is None:
        return {'matches': [], 'errors': ['Failed to parse LLM output as JSON']}

    if not isinstance(parsed, list):
        return {'matches': [], 'errors': ['LLM output is not a JSON array']}

    trace_ids = {t.get('id', t.get('sentence_id', '')) for t in traces}

    for i, entry in enumerate(parsed):
        if not isinstance(entry, dict):
            errors.append(f'Entry {i}: not a dict')
            continue

        sid = entry.get('sentence_id', entry.get('id', entry.get('trace_id', '')))
        if not sid:
            errors.append(f'Entry {i}: missing sentence_id/id')
            continue

        status = entry.get('status', '').upper()
        if status not in VALID_STATUSES:
            errors.append(f'Entry {i} ({sid}): invalid status "{status}"')
            continue

        match = {
            'trace_id': sid,
            'status': status,
            'spec_ref': entry.get('spec_ref', ''),
            'notes': entry.get('notes', ''),
        }

        if entry.get('refs'):
            match['refs'] = entry['refs']

        matches.append(match)

    matched_ids = {m['trace_id'] for m in matches}
    unmatched = trace_ids - matched_ids
    if unmatched:
        errors.append(f'Traces not matched by LLM: {sorted(unmatched)}')

    return {'matches': matches, 'errors': errors}


def apply_matches(traces: list[dict], matches: list[dict]) -> list[dict]:
    """Apply coverage match results to traces."""
    match_map = {}
    for m in matches:
        key = m.get('trace_id', m.get('sentence_id', m.get('id', '')))
        match_map[key] = m

    result = []
    for trace in traces:
        t = dict(trace)
        tid = t.get('id', t.get('sentence_id', ''))
        match = match_map.get(tid)

        if match:
            t['status'] = match['status']
            refs = []
            if match.get('spec_ref'):
                refs.append(_parse_spec_ref(match['spec_ref']))
            if match.get('refs'):
                refs.extend(match['refs'])
            t['refs'] = refs
            if match.get('notes'):
                t['notes'] = match['notes']
        else:
            t['status'] = 'MISSING'
            t['refs'] = []

        result.append(t)

    return result


def format_reverse_prompt(
    reverse_traces: list[dict],
    source_traces: list[dict],
    language: str = 'hu',
) -> str:
    """Format reverse matching prompt (target claims vs source traces).

    Args:
        reverse_traces: target-extracted claims to check
        source_traces: source traces as evidence
        language: 'hu' or 'en'
    """
    if language == 'en':
        template_path = PROMPT_TEMPLATE_PATH / 'en' / 'reverse_check.txt'
    else:
        template_path = PROMPT_TEMPLATE_PATH / 'reverse_check.txt'

    template = template_path.read_text(encoding='utf-8')

    claim_lines = []
    for t in reverse_traces:
        tid = t.get('id', '')
        text = t.get('text', '')
        ttype = t.get('type', 'REQUIREMENT')
        claim_lines.append(f"[{tid}] ({ttype}) {text}")

    evidence_lines = []
    for t in source_traces:
        tid = t.get('id', '')
        text = t.get('text', '')
        ttype = t.get('type', 'REQUIREMENT')
        implicit = ' [implicit]' if t.get('implicit') else ''
        evidence_lines.append(f"[{tid}] ({ttype}{implicit}) {text}")

    prompt = template.replace('{claims}', '\n'.join(claim_lines))
    prompt = prompt.replace('{evidence}', '\n'.join(evidence_lines))
    return prompt


def validate_reverse_matches(raw_output: str, reverse_traces: list[dict]) -> dict:
    """Validate LLM reverse matching output.

    Returns:
        dict with 'matches' and 'errors'
    """
    errors = []
    matches = []

    parsed = _parse_json_output(raw_output)
    if parsed is None:
        return {'matches': [], 'errors': ['Failed to parse LLM output as JSON']}

    if not isinstance(parsed, list):
        return {'matches': [], 'errors': ['LLM output is not a JSON array']}

    claim_ids = {t.get('id', '') for t in reverse_traces}

    for i, entry in enumerate(parsed):
        if not isinstance(entry, dict):
            errors.append(f'Entry {i}: not a dict')
            continue

        cid = entry.get('claim_id', entry.get('id', entry.get('trace_id', '')))
        if not cid:
            errors.append(f'Entry {i}: missing claim_id')
            continue

        status = entry.get('status', '').upper()
        if status not in VALID_REVERSE_STATUSES:
            errors.append(f'Entry {i} ({cid}): invalid status "{status}"')
            continue

        match = {
            'claim_id': cid,
            'status': status,
            'source_trace_id': entry.get('source_trace_id'),
            'nearest_source_trace': entry.get('nearest_source_trace'),
            'similarity_note': entry.get('similarity_note', ''),
            'notes': entry.get('notes', ''),
        }
        matches.append(match)

    matched_ids = {m['claim_id'] for m in matches}
    unmatched = claim_ids - matched_ids
    if unmatched:
        errors.append(f'Claims not matched by LLM: {sorted(unmatched)}')

    return {'matches': matches, 'errors': errors}


def apply_reverse_matches(reverse_traces: list[dict], matches: list[dict]) -> list[dict]:
    """Apply reverse match results to target-extracted traces."""
    match_map = {m['claim_id']: m for m in matches}

    result = []
    for trace in reverse_traces:
        t = dict(trace)
        tid = t.get('id', '')
        match = match_map.get(tid)

        if match:
            t['status'] = match['status']
            t['nearest_source_trace'] = match.get('nearest_source_trace')
            t['similarity_note'] = match.get('similarity_note', '')
            if match.get('source_trace_id'):
                t['source_trace_id'] = match['source_trace_id']
            if match.get('notes'):
                t['notes'] = match['notes']
        else:
            t['status'] = 'UNTRACED_IN_SOURCE'
            t['nearest_source_trace'] = None
            t['similarity_note'] = 'not evaluated by LLM'

        result.append(t)

    return result


def _parse_spec_ref(ref_str: str) -> dict:
    """Parse a spec reference string like 'target.md §2.1' into a dict."""
    parts = ref_str.split('§')
    file_part = parts[0].strip() if parts else ''
    section = f'§{parts[1].strip()}' if len(parts) > 1 else ''
    return {
        'file': file_part,
        'section': section,
        'line': 0,
    }


def resolve_refs(traces: list[dict], target_files: list[str]) -> list[dict]:
    """Resolve section references to file + line number in target documents."""
    section_index = {}
    for tf in target_files:
        try:
            lines = Path(tf).read_text(encoding='utf-8').split('\n')
        except OSError:
            continue
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r'^#{1,4}\s+', stripped):
                section_index[(tf, stripped)] = i + 1

    for trace in traces:
        for ref in trace.get('refs', []):
            if ref.get('line', 0) > 0 and ref.get('file'):
                continue
            section = ref.get('section', '')
            if not section:
                continue
            best_file = ''
            best_line = 0
            for (tf, header), lineno in section_index.items():
                if _section_matches(section, header):
                    best_file = tf
                    best_line = lineno
                    break
            if best_line:
                if not ref.get('file'):
                    ref['file'] = best_file
                ref['line'] = best_line

    return traces


def _section_matches(section_ref: str, header_line: str) -> bool:
    """Check if a section reference matches a markdown header."""
    clean_ref = section_ref.lstrip('§').strip().lower()
    clean_header = re.sub(r'^#+\s*', '', header_line).strip().lower()
    return clean_ref in clean_header or clean_header in clean_ref


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


def main():
    if len(sys.argv) < 3:
        print("Usage: coverage.py <mode> <args...>", file=sys.stderr)
        print("Modes:", file=sys.stderr)
        print("  format-prompt <traces.json> <target.md> [--lang hu|en] [--exclusions <text>]", file=sys.stderr)
        print("  validate <raw_output.txt> <traces.json>", file=sys.stderr)
        print("  apply <traces.json> <matches.json>", file=sys.stderr)
        print("  sections <target.md>  — parse target into sections (debug)", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == 'format-prompt':
        traces_data = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
        traces = traces_data.get('traces', traces_data) if isinstance(traces_data, dict) else traces_data
        target_text = Path(sys.argv[3]).read_text(encoding='utf-8')

        lang = 'hu'
        exclusions = ''
        args = sys.argv[4:]
        for i, arg in enumerate(args):
            if arg == '--lang' and i + 1 < len(args):
                lang = args[i + 1]
            elif arg == '--exclusions' and i + 1 < len(args):
                exclusions = args[i + 1]

        batches = batch_traces(traces)
        if len(batches) == 1:
            prompt = format_prompt(traces, target_text, exclusions, lang)
            print(prompt)
        else:
            for bi, batch in enumerate(batches):
                print(f"--- BATCH {bi + 1}/{len(batches)} ---", file=sys.stderr)
                prompt = format_prompt(batch, target_text, exclusions, lang)
                print(prompt)
                if bi < len(batches) - 1:
                    print('\n---BATCH_SEPARATOR---\n')

    elif mode == 'validate':
        raw_output = Path(sys.argv[2]).read_text(encoding='utf-8')
        traces_data = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
        traces = traces_data.get('traces', traces_data) if isinstance(traces_data, dict) else traces_data

        result = validate_matches(raw_output, traces)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)

    elif mode == 'apply':
        traces_data = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
        traces = traces_data.get('traces', traces_data) if isinstance(traces_data, dict) else traces_data
        matches_data = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
        matches = matches_data.get('matches', matches_data) if isinstance(matches_data, dict) else matches_data

        result = apply_matches(traces, matches)
        json.dump({'traces': result}, sys.stdout, ensure_ascii=False, indent=2)

    elif mode == 'reverse-prompt':
        reverse_data = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
        reverse_traces = reverse_data.get('traces', reverse_data) if isinstance(reverse_data, dict) else reverse_data
        source_data = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
        source_traces = source_data.get('traces', source_data) if isinstance(source_data, dict) else source_data

        lang = 'hu'
        for i, arg in enumerate(sys.argv[4:]):
            if arg == '--lang' and i + 5 <= len(sys.argv):
                lang = sys.argv[i + 5]

        batches = batch_traces(reverse_traces)
        if len(batches) == 1:
            prompt = format_reverse_prompt(reverse_traces, source_traces, lang)
            print(prompt)
        else:
            for bi, batch in enumerate(batches):
                print(f"--- BATCH {bi + 1}/{len(batches)} ---", file=sys.stderr)
                prompt = format_reverse_prompt(batch, source_traces, lang)
                print(prompt)
                if bi < len(batches) - 1:
                    print('\n---BATCH_SEPARATOR---\n')

    elif mode == 'reverse-validate':
        raw_output = Path(sys.argv[2]).read_text(encoding='utf-8')
        reverse_data = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
        reverse_traces = reverse_data.get('traces', reverse_data) if isinstance(reverse_data, dict) else reverse_data

        result = validate_reverse_matches(raw_output, reverse_traces)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)

    elif mode == 'reverse-apply':
        reverse_data = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
        reverse_traces = reverse_data.get('traces', reverse_data) if isinstance(reverse_data, dict) else reverse_data
        matches_data = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
        matches = matches_data.get('matches', matches_data) if isinstance(matches_data, dict) else matches_data

        result = apply_reverse_matches(reverse_traces, matches)
        json.dump({'traces': result}, sys.stdout, ensure_ascii=False, indent=2)

    elif mode == 'sections':
        target_text = Path(sys.argv[2]).read_text(encoding='utf-8')
        target_file = sys.argv[2]
        sections = parse_target_sections(target_text, target_file)
        json.dump(sections, sys.stdout, ensure_ascii=False, indent=2)

    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
