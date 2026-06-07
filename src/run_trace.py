#!/usr/bin/env python3
"""End-to-end trace pipeline runner.

This script orchestrates the full pipeline:
  source.md + target.md → trace-map.json

It runs the deterministic steps (clause_split, remainder, trace_map)
directly, and prints the prompts that need to be sent to LLM subagents.
The Claude Code agent calls this script, sends prompts to subagents,
and feeds responses back.

Usage (by the agent):
  # Step 1: Split clauses
  python3 src/run_trace.py split <source.md> [--lang hu|en]

  # Step 2: Format extraction prompt
  python3 src/run_trace.py extract-prompt <clauses.json> [--lang hu|en] [--source <file>]

  # Step 3: Validate extraction output
  python3 src/run_trace.py extract-validate <llm_output.txt> <clauses.json> [--source <file>]

  # Step 4: Compute remainder
  python3 src/run_trace.py remainder <clauses.json> <traces.json>

  # Step 5: Format coverage prompt
  python3 src/run_trace.py match-prompt <traces.json> <target.md> [--lang hu|en]

  # Step 6: Validate match output
  python3 src/run_trace.py match-validate <llm_output.txt> <traces.json>

  # Step 7: Apply matches and generate trace-map
  python3 src/run_trace.py finalize <traces.json> <matches.json> --source <file> --target <file> [--output trace-map.json]

  # Or: run the full deterministic pipeline (agent handles LLM steps)
  python3 src/run_trace.py status <traces.json> <clauses.json>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parse.clause_split import process_document
from extract.extract import format_prompt as extract_format_prompt, validate_traces, merge_traces
from extract.remainder import compute_remainder, is_complete, extraction_stats
from match.coverage import format_prompt as match_format_prompt, validate_matches, apply_matches
from output.trace_map import build_trace_map


def cmd_split(args):
    """Split source document into clauses."""
    source_path = Path(args[0])
    text = source_path.read_text(encoding='utf-8')
    clauses = process_document(text)

    content_clauses = [c for c in clauses if not c.get('is_header')]
    compound_lines = set()
    for c in content_clauses:
        if c['clause_index'] > 0:
            compound_lines.add(c['line_number'])

    result = {
        'source_file': str(source_path),
        'total_lines': len(text.split('\n')),
        'content_clauses': len(content_clauses),
        'compound_lines_split': len(compound_lines),
        'clauses': clauses,
    }

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


def cmd_extract_prompt(args):
    """Format extraction prompt from clauses."""
    clauses_data = json.loads(Path(args[0]).read_text(encoding='utf-8'))
    clauses = clauses_data.get('clauses', clauses_data) if isinstance(clauses_data, dict) else clauses_data

    lang = 'hu'
    source_file = ''
    for i, arg in enumerate(args[1:]):
        if arg == '--lang' and i + 2 <= len(args):
            lang = args[i + 2]
        elif arg == '--source' and i + 2 <= len(args):
            source_file = args[i + 2]

    prompt = extract_format_prompt(clauses, source_file, lang)
    print(prompt)


def cmd_extract_validate(args):
    """Validate LLM extraction output."""
    raw_output = Path(args[0]).read_text(encoding='utf-8')
    clauses_data = json.loads(Path(args[1]).read_text(encoding='utf-8'))
    clauses = clauses_data.get('clauses', clauses_data) if isinstance(clauses_data, dict) else clauses_data

    source_file = ''
    for i, arg in enumerate(args[2:]):
        if arg == '--source' and i + 3 <= len(args):
            source_file = args[i + 3]

    result = validate_traces(raw_output, clauses, source_file)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


def cmd_remainder(args):
    """Compute remainder after extraction."""
    clauses_data = json.loads(Path(args[0]).read_text(encoding='utf-8'))
    clauses = clauses_data.get('clauses', clauses_data) if isinstance(clauses_data, dict) else clauses_data
    traces_data = json.loads(Path(args[1]).read_text(encoding='utf-8'))
    traces = traces_data.get('traces', traces_data) if isinstance(traces_data, dict) else traces_data

    content_clauses = [c for c in clauses if not c.get('is_header')]
    remainder = compute_remainder(content_clauses, traces)
    stats = extraction_stats(content_clauses, traces, remainder)
    complete = is_complete(remainder, None)

    result = {
        'stats': stats,
        'remainder': remainder,
        'complete': complete,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


def cmd_match_prompt(args):
    """Format coverage matching prompt."""
    traces_data = json.loads(Path(args[0]).read_text(encoding='utf-8'))
    traces = traces_data.get('traces', traces_data) if isinstance(traces_data, dict) else traces_data
    target_text = Path(args[1]).read_text(encoding='utf-8')

    lang = 'hu'
    exclusions = ''
    for i, arg in enumerate(args[2:]):
        if arg == '--lang' and i + 3 <= len(args):
            lang = args[i + 3]
        elif arg == '--exclusions' and i + 3 <= len(args):
            exclusions = args[i + 3]

    prompt = match_format_prompt(traces, target_text, exclusions, lang)
    print(prompt)


def cmd_match_validate(args):
    """Validate LLM matching output."""
    raw_output = Path(args[0]).read_text(encoding='utf-8')
    traces_data = json.loads(Path(args[1]).read_text(encoding='utf-8'))
    traces = traces_data.get('traces', traces_data) if isinstance(traces_data, dict) else traces_data

    result = validate_matches(raw_output, traces)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


def cmd_finalize(args):
    """Apply matches and generate trace-map.json."""
    traces_data = json.loads(Path(args[0]).read_text(encoding='utf-8'))
    traces = traces_data.get('traces', traces_data) if isinstance(traces_data, dict) else traces_data
    matches_data = json.loads(Path(args[1]).read_text(encoding='utf-8'))
    matches = matches_data.get('matches', matches_data) if isinstance(matches_data, dict) else matches_data

    source_files = []
    target_files = []
    untraced = []
    output_path = None

    i = 2
    while i < len(args):
        if args[i] == '--source':
            source_files.append(args[i + 1])
            i += 2
        elif args[i] == '--target':
            target_files.append(args[i + 1])
            i += 2
        elif args[i] == '--output':
            output_path = Path(args[i + 1])
            i += 2
        elif args[i] == '--untraced':
            untraced_data = json.loads(Path(args[i + 1]).read_text(encoding='utf-8'))
            untraced = untraced_data.get('remainder', untraced_data) if isinstance(untraced_data, dict) else untraced_data
            i += 2
        else:
            i += 1

    matched_traces = apply_matches(traces, matches)
    trace_map = build_trace_map(matched_traces, source_files, target_files, untraced)

    output_json = json.dumps(trace_map, ensure_ascii=False, indent=2)
    if output_path:
        output_path.write_text(output_json, encoding='utf-8')
        print(f"Written to {output_path}", file=sys.stderr)
        summary = trace_map['summary']
        print(f"Coverage: {summary['coverage_score_pct']}% "
              f"({summary['covered']}C/{summary['partial']}P/{summary['missing']}M/"
              f"{summary['deferred']}D)", file=sys.stderr)
    else:
        print(output_json)


def cmd_status(args):
    """Show pipeline status."""
    traces_data = json.loads(Path(args[0]).read_text(encoding='utf-8'))
    traces = traces_data.get('traces', traces_data) if isinstance(traces_data, dict) else traces_data
    clauses_data = json.loads(Path(args[1]).read_text(encoding='utf-8'))
    clauses = clauses_data.get('clauses', clauses_data) if isinstance(clauses_data, dict) else clauses_data

    content_clauses = [c for c in clauses if not c.get('is_header')]
    remainder = compute_remainder(content_clauses, traces)
    stats = extraction_stats(content_clauses, traces, remainder)

    has_status = any('status' in t for t in traces)

    print(f"Clauses: {stats['total_clauses']}", file=sys.stderr)
    print(f"Traces extracted: {stats['traces_extracted']}", file=sys.stderr)
    print(f"Clauses consumed: {stats['clauses_consumed']}/{stats['total_clauses']} "
          f"({stats['coverage_pct']:.1f}%)", file=sys.stderr)
    print(f"Remainder: {stats['clauses_remaining']} clauses", file=sys.stderr)
    print(f"Extraction complete: {stats['complete']}", file=sys.stderr)

    if has_status:
        from output.trace_map import compute_summary
        summary = compute_summary(traces)
        print(f"\nCoverage matching:", file=sys.stderr)
        print(f"  Score: {summary['coverage_score_pct']}%", file=sys.stderr)
        print(f"  COVERED: {summary['covered']}", file=sys.stderr)
        print(f"  PARTIAL: {summary['partial']}", file=sys.stderr)
        print(f"  MISSING: {summary['missing']}", file=sys.stderr)
        print(f"  DEFERRED: {summary['deferred']}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        'split': cmd_split,
        'extract-prompt': cmd_extract_prompt,
        'extract-validate': cmd_extract_validate,
        'remainder': cmd_remainder,
        'match-prompt': cmd_match_prompt,
        'match-validate': cmd_match_validate,
        'finalize': cmd_finalize,
        'status': cmd_status,
    }

    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(f"Available: {', '.join(commands)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
