import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROMPT_TEMPLATE_PATH = resolve(__dirname, '..', '..', 'prompts');

export const VALID_STATUSES = new Set([
  'COVERED', 'PARTIAL', 'MISSING', 'DEFERRED', 'N/A',
] as const);

export type CoverageStatus = 'COVERED' | 'PARTIAL' | 'MISSING' | 'DEFERRED' | 'N/A';

export const VALID_REVERSE_STATUSES = new Set([
  'TRACED', 'PARTIAL_SOURCE', 'UNTRACED_IN_SOURCE',
] as const);

export type ReverseStatus = 'TRACED' | 'PARTIAL_SOURCE' | 'UNTRACED_IN_SOURCE';

export const MAX_TRACES_PER_BATCH = 20;

export interface TargetSection {
  id: string;
  title: string;
  file: string;
  line: number;
  text: string;
}

export interface SpecRef {
  file: string;
  section: string;
  line: number;
}

export interface Match {
  trace_id: string;
  status: string;
  spec_ref: string;
  notes: string;
  refs?: unknown[];
}

export interface ReverseMatch {
  claim_id: string;
  status: string;
  source_trace_id: string | undefined;
  nearest_source_trace: string | undefined;
  similarity_note: string;
  notes: string;
}

export interface MatchValidationResult {
  matches: Match[];
  errors: string[];
}

export interface ReverseMatchValidationResult {
  matches: ReverseMatch[];
  errors: string[];
}

interface TraceInput {
  id?: string;
  sentence_id?: string;
  text?: string;
  type?: string;
  implicit?: boolean;
  status?: string;
  source?: Record<string, unknown>;
  refs?: unknown[];
  nearest_source_trace?: string;
  similarity_note?: string;
  [key: string]: unknown;
}

export function parseTargetSections(targetText: string, targetFile: string = ''): TargetSection[] {
  const sections: TargetSection[] = [];
  let currentSection: TargetSection | null = null;
  let currentLines: string[] = [];

  const lines = targetText.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const stripped = line.trim();

    let headerMatch = stripped.match(/^(#{1,4})\s+(.+)$/);
    let sectionMatch: RegExpMatchArray | null = null;
    if (!headerMatch) {
      sectionMatch = stripped.match(/^(\d+(?:\.\d+)*)\s+(.+)$/);
    }

    const match = headerMatch ?? sectionMatch;

    if (match) {
      if (currentSection) {
        currentSection.text = currentLines.join('\n').trim();
        if (currentSection.text) {
          sections.push(currentSection);
        }
      }

      const title = match[2];
      let sectionId = match[1];
      if (sectionId.startsWith('#')) {
        sectionId = `§${sectionId.length}`;
      }

      currentSection = {
        id: sectionId,
        title,
        file: targetFile,
        line: i + 1,
        text: '',
      };
      currentLines = [line];
    } else if (currentSection) {
      currentLines.push(line);
    } else if (stripped) {
      if (!currentSection) {
        currentSection = {
          id: '§0',
          title: '(preamble)',
          file: targetFile,
          line: 1,
          text: '',
        };
        currentLines = [];
      }
      currentLines.push(line);
    }
  }

  if (currentSection) {
    currentSection.text = currentLines.join('\n').trim();
    if (currentSection.text) {
      sections.push(currentSection);
    }
  }

  return sections;
}

export function formatPrompt(
  traces: TraceInput[],
  targetText: string,
  exclusions: string = '',
  language: string = 'hu',
): string {
  const templatePath = language === 'en'
    ? resolve(PROMPT_TEMPLATE_PATH, 'en', 'coverage_check.txt')
    : resolve(PROMPT_TEMPLATE_PATH, 'coverage_check.txt');

  const template = readFileSync(templatePath, 'utf-8');

  const reqLines: string[] = [];
  for (const t of traces) {
    const tid = t.id ?? t.sentence_id ?? '';
    const text = t.text ?? '';
    const ttype = t.type ?? 'REQUIREMENT';
    const implicit = t.implicit ? ' [implicit]' : '';
    reqLines.push(`[${tid}] (${ttype}${implicit}) ${text}`);
  }

  let prompt = template.replace('{requirements}', reqLines.join('\n'));
  prompt = prompt.replace('{specs}', targetText);
  prompt = prompt.replace('{exclusions}', exclusions || '(none specified)');

  return prompt;
}

export function batchTraces<T>(traces: T[], batchSize: number = MAX_TRACES_PER_BATCH): T[][] {
  const batches: T[][] = [];
  for (let i = 0; i < traces.length; i += batchSize) {
    batches.push(traces.slice(i, i + batchSize));
  }
  return batches;
}

export function validateMatches(rawOutput: string, traces: TraceInput[], validStatuses: Set<string> = VALID_STATUSES as Set<string>): MatchValidationResult {
  const errors: string[] = [];
  const matches: Match[] = [];

  const parsed = parseJsonOutput(rawOutput);
  if (parsed === null) {
    return { matches: [], errors: ['Failed to parse LLM output as JSON'] };
  }
  if (!Array.isArray(parsed)) {
    return { matches: [], errors: ['LLM output is not a JSON array'] };
  }

  const traceIds = new Set<string>();
  for (const t of traces) {
    traceIds.add(t.id ?? t.sentence_id ?? '');
  }

  for (let i = 0; i < parsed.length; i++) {
    const entry = parsed[i];
    if (typeof entry !== 'object' || entry === null || Array.isArray(entry)) {
      errors.push(`Entry ${i}: not a dict`);
      continue;
    }

    const rec = entry as Record<string, unknown>;
    const sid = (rec.sentence_id ?? rec.id ?? rec.trace_id ?? '') as string;
    if (!sid) {
      errors.push(`Entry ${i}: missing sentence_id/id`);
      continue;
    }

    const status = ((rec.status as string) ?? '').toUpperCase();
    if (!validStatuses.has(status)) {
      errors.push(`Entry ${i} (${sid}): invalid status "${status}"`);
      continue;
    }

    const match: Match = {
      trace_id: sid,
      status,
      spec_ref: (rec.spec_ref as string) ?? '',
      notes: (rec.notes as string) ?? '',
    };

    if (rec.refs) {
      match.refs = rec.refs as unknown[];
    }

    matches.push(match);
  }

  const matchedIds = new Set(matches.map(m => m.trace_id));
  const unmatched = [...traceIds].filter(id => !matchedIds.has(id)).sort();
  if (unmatched.length > 0) {
    errors.push(`Traces not matched by LLM: ${JSON.stringify(unmatched)}`);
  }

  return { matches, errors };
}

export function applyMatches(traces: TraceInput[], matches: Match[]): TraceInput[] {
  const matchMap = new Map<string, Match>();
  for (const m of matches) {
    const key = m.trace_id;
    matchMap.set(key, m);
  }

  const result: TraceInput[] = [];
  for (const trace of traces) {
    const t = { ...trace };
    const tid = t.id ?? t.sentence_id ?? '';
    const match = matchMap.get(tid);

    if (match) {
      t.status = match.status;
      const refs: unknown[] = [];
      if (match.spec_ref) {
        refs.push(parseSpecRef(match.spec_ref));
      }
      if (match.refs) {
        refs.push(...match.refs);
      }
      t.refs = refs;
      if (match.notes) {
        t.notes = match.notes;
      }
    } else {
      t.status = 'MISSING';
      t.refs = [];
    }

    result.push(t);
  }

  return result;
}

export function formatReversePrompt(
  reverseTraces: TraceInput[],
  sourceTraces: TraceInput[],
  language: string = 'hu',
): string {
  const templatePath = language === 'en'
    ? resolve(PROMPT_TEMPLATE_PATH, 'en', 'reverse_check.txt')
    : resolve(PROMPT_TEMPLATE_PATH, 'reverse_check.txt');

  const template = readFileSync(templatePath, 'utf-8');

  const claimLines: string[] = [];
  for (const t of reverseTraces) {
    const tid = t.id ?? '';
    const text = t.text ?? '';
    const ttype = t.type ?? 'REQUIREMENT';
    claimLines.push(`[${tid}] (${ttype}) ${text}`);
  }

  const evidenceLines: string[] = [];
  for (const t of sourceTraces) {
    const tid = t.id ?? '';
    const text = t.text ?? '';
    const ttype = t.type ?? 'REQUIREMENT';
    const implicit = t.implicit ? ' [implicit]' : '';
    evidenceLines.push(`[${tid}] (${ttype}${implicit}) ${text}`);
  }

  let prompt = template.replace('{claims}', claimLines.join('\n'));
  prompt = prompt.replace('{evidence}', evidenceLines.join('\n'));
  return prompt;
}

export function validateReverseMatches(
  rawOutput: string,
  reverseTraces: TraceInput[],
): ReverseMatchValidationResult {
  const errors: string[] = [];
  const matches: ReverseMatch[] = [];

  const parsed = parseJsonOutput(rawOutput);
  if (parsed === null) {
    return { matches: [], errors: ['Failed to parse LLM output as JSON'] };
  }
  if (!Array.isArray(parsed)) {
    return { matches: [], errors: ['LLM output is not a JSON array'] };
  }

  const claimIds = new Set<string>();
  for (const t of reverseTraces) {
    claimIds.add(t.id ?? '');
  }

  for (let i = 0; i < parsed.length; i++) {
    const entry = parsed[i];
    if (typeof entry !== 'object' || entry === null || Array.isArray(entry)) {
      errors.push(`Entry ${i}: not a dict`);
      continue;
    }

    const rec = entry as Record<string, unknown>;
    const cid = (rec.claim_id ?? rec.id ?? rec.trace_id ?? '') as string;
    if (!cid) {
      errors.push(`Entry ${i}: missing claim_id`);
      continue;
    }

    const status = ((rec.status as string) ?? '').toUpperCase();
    if (!VALID_REVERSE_STATUSES.has(status as ReverseStatus)) {
      errors.push(`Entry ${i} (${cid}): invalid status "${status}"`);
      continue;
    }

    const match: ReverseMatch = {
      claim_id: cid,
      status,
      source_trace_id: rec.source_trace_id as string | undefined,
      nearest_source_trace: rec.nearest_source_trace as string | undefined,
      similarity_note: (rec.similarity_note as string) ?? '',
      notes: (rec.notes as string) ?? '',
    };
    matches.push(match);
  }

  const matchedIds = new Set(matches.map(m => m.claim_id));
  const unmatched = [...claimIds].filter(id => !matchedIds.has(id)).sort();
  if (unmatched.length > 0) {
    errors.push(`Claims not matched by LLM: ${JSON.stringify(unmatched)}`);
  }

  return { matches, errors };
}

export function applyReverseMatches(
  reverseTraces: TraceInput[],
  matches: ReverseMatch[],
): TraceInput[] {
  const matchMap = new Map<string, ReverseMatch>();
  for (const m of matches) {
    matchMap.set(m.claim_id, m);
  }

  const result: TraceInput[] = [];
  for (const trace of reverseTraces) {
    const t = { ...trace };
    const tid = t.id ?? '';
    const match = matchMap.get(tid);

    if (match) {
      t.status = match.status;
      t.nearest_source_trace = match.nearest_source_trace;
      t.similarity_note = match.similarity_note;
      if (match.source_trace_id) {
        t.source_trace_id = match.source_trace_id;
      }
      if (match.notes) {
        t.notes = match.notes;
      }
    } else {
      t.status = 'UNTRACED_IN_SOURCE';
      t.nearest_source_trace = undefined;
      t.similarity_note = 'not evaluated by LLM';
    }

    result.push(t);
  }

  return result;
}

export function resolveRefs(traces: TraceInput[], targetFiles: string[]): TraceInput[] {
  const sectionIndex = new Map<string, number>();

  for (const tf of targetFiles) {
    let lines: string[];
    try {
      lines = readFileSync(tf, 'utf-8').split('\n');
    } catch {
      continue;
    }
    for (let i = 0; i < lines.length; i++) {
      const stripped = lines[i].trim();
      if (/^#{1,4}\s+/.test(stripped)) {
        sectionIndex.set(`${tf}\0${stripped}`, i + 1);
      }
    }
  }

  for (const trace of traces) {
    const refs = trace.refs as SpecRef[] | undefined;
    if (!refs) continue;

    for (const ref of refs) {
      const fileIsReal = (ref.file ?? '').match(/\.(md|txt|json)$/);
      if ((ref.line ?? 0) > 0 && fileIsReal) {
        continue;
      }
      const section = ref.section ?? '';
      if (!section) continue;

      let bestFile = '';
      let bestLine = 0;
      for (const [key, lineno] of sectionIndex) {
        const [tf, header] = key.split('\0');
        if (sectionMatches(section, header)) {
          bestFile = tf;
          bestLine = lineno;
          break;
        }
      }
      if (bestLine) {
        ref.file = bestFile;
        ref.line = bestLine;
      }
    }
  }

  return traces;
}

function parseSpecRef(refStr: string): SpecRef {
  const parts = refStr.split('§');
  const filePart = parts.length > 0 ? parts[0].trim() : '';
  const section = parts.length > 1 ? `§${parts[1].trim()}` : '';
  return {
    file: filePart,
    section,
    line: 0,
  };
}

function sectionMatches(sectionRef: string, headerLine: string): boolean {
  const cleanRef = sectionRef.replace(/^§\s*/, '').trim().toLowerCase();
  const cleanHeader = headerLine.replace(/^#+\s*/, '').trim().toLowerCase();
  return cleanRef.includes(cleanHeader) || cleanHeader.includes(cleanRef);
}

export function parseJsonOutput(raw: string): unknown[] | null {
  raw = raw.trim();

  if (raw.startsWith('```json')) {
    raw = raw.slice(7);
  }
  if (raw.startsWith('```')) {
    raw = raw.slice(3);
  }
  if (raw.endsWith('```')) {
    raw = raw.slice(0, -3);
  }
  raw = raw.trim();

  try {
    return JSON.parse(raw);
  } catch {
    // fall through
  }

  const start = raw.indexOf('[');
  const end = raw.lastIndexOf(']');
  if (start !== -1 && end !== -1 && end > start) {
    try {
      return JSON.parse(raw.slice(start, end + 1));
    } catch {
      // fall through
    }
  }

  return null;
}
