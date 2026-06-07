import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';

export const VALID_TYPES = new Set([
  'REQUIREMENT', 'DECISION', 'WISH', 'OPEN_QUESTION', 'EXCLUSION',
] as const);

export type TraceType = 'REQUIREMENT' | 'DECISION' | 'WISH' | 'OPEN_QUESTION' | 'EXCLUSION';

export interface TraceSource {
  file: string;
  line: number;
  col_start: number;
  col_end: number;
}

export interface Trace {
  id: string;
  text: string;
  type: TraceType;
  source: TraceSource;
  clause_id: string;
  clause_ids: string[];
  topics: string[];
  implicit: boolean;
  triple?: unknown;
  signal?: string;
}

export interface Clause {
  clause_id: string;
  text: string;
  line_number: number;
  clause_index: number;
  is_header?: boolean;
  is_meta?: boolean;
}

export interface ValidationResult {
  traces: Trace[];
  errors: string[];
}

export function formatPrompt(
  clauses: Clause[],
  sourceFile: string = '',
  language: string = 'hu',
  pkgRoot: string,
): string {
  const templatePath = language === 'en'
    ? resolve(pkgRoot, 'prompts', 'en', 'extract.txt')
    : resolve(pkgRoot, 'prompts', 'extract.txt');

  const template = readFileSync(templatePath, 'utf-8');

  const clauseLines: string[] = [];
  for (const c of clauses) {
    if (c.is_header || c.is_meta) continue;
    clauseLines.push(`[${c.clause_id}] ${c.text}`);
  }

  return template.replace('{clauses}', clauseLines.join('\n'));
}

export function sourceHash(filepath: string): string {
  return createHash('sha256').update(filepath, 'utf-8').digest('hex').slice(0, 6);
}

export function validateTraces(
  rawOutput: string,
  clauses: Clause[],
  sourceFile: string = '',
  idPrefix: string = 'T',
): ValidationResult {
  const errors: string[] = [];
  const traces: Trace[] = [];

  const parsed = parseJsonOutput(rawOutput);
  if (parsed === null) {
    return { traces: [], errors: ['Failed to parse LLM output as JSON'] };
  }
  if (!Array.isArray(parsed)) {
    return { traces: [], errors: ['LLM output is not a JSON array'] };
  }

  const clauseMap = new Map<string, Clause>();
  for (const c of clauses) {
    if (!c.is_header && !c.is_meta) {
      clauseMap.set(c.clause_id, c);
    }
  }

  const fileHash = sourceHash(sourceFile);
  const idCounter = new Map<string, number>();

  for (let i = 0; i < parsed.length; i++) {
    const raw = parsed[i];
    if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
      errors.push(`Entry ${i}: not a dict`);
      continue;
    }
    const entry = raw as Record<string, unknown>;

    let clauseId = entry.clause_id as string | undefined;
    if (!clauseId) {
      const clauseIds = (entry.clause_ids ?? []) as string[];
      if (clauseIds.length > 0) {
        clauseId = clauseIds[0];
      } else {
        errors.push(`Entry ${i}: missing clause_id`);
        continue;
      }
    }

    let traceType = ((entry.type as string | undefined) ?? '').toUpperCase() as TraceType;
    if (!VALID_TYPES.has(traceType)) {
      errors.push(`Entry ${i}: invalid type "${traceType}"`);
      traceType = 'REQUIREMENT';
    }

    const text = ((entry.text as string | undefined) ?? '');
    if (!text) {
      errors.push(`Entry ${i}: missing text`);
      continue;
    }

    const clause = clauseMap.get(clauseId);
    const lineNum = clause ? clause.line_number : 0;
    const clauseIdx = clause ? clause.clause_index : 0;

    const baseId = `${idPrefix}-${fileHash}-${String(lineNum).padStart(3, '0')}-${clauseIdx}`;
    const seq = idCounter.get(baseId) ?? 0;
    idCounter.set(baseId, seq + 1);
    const traceId = seq === 0 ? baseId : `${baseId}-${seq}`;

    const trace: Trace = {
      id: traceId,
      text,
      type: traceType,
      source: {
        file: sourceFile,
        line: lineNum,
        col_start: 0,
        col_end: clause ? clause.text.length : text.length,
      },
      clause_id: clauseId,
      clause_ids: (entry.clause_ids ?? [clauseId]) as string[],
      topics: ((entry.tags ?? entry.topics ?? []) as string[]),
      implicit: (entry.implicit ?? false) as boolean,
      triple: entry.triple,
    };

    if (entry.signal) {
      trace.signal = entry.signal as string;
    }

    traces.push(trace);
  }

  return { traces, errors };
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
    const result = JSON.parse(raw);
    return result;
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

export function mergeTraces(existing: Trace[], newTraces: Trace[]): Trace[] {
  const existingClauseIds = new Set<string>();
  for (const t of existing) {
    if (t.clause_id) existingClauseIds.add(t.clause_id);
    if (t.clause_ids) {
      for (const id of t.clause_ids) existingClauseIds.add(id);
    }
  }

  const merged = [...existing];
  for (const t of newTraces) {
    const tIds = new Set(t.clause_ids ?? [t.clause_id ?? '']);
    let allExist = true;
    for (const id of tIds) {
      if (!existingClauseIds.has(id)) {
        allExist = false;
        break;
      }
    }
    if (!allExist) {
      merged.push(t);
      for (const id of tIds) existingClauseIds.add(id);
    }
  }

  return merged;
}
