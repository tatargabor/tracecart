import type { Clause, Trace } from './extract.js';

export interface ExtractionStats {
  total_clauses: number;
  traces_extracted: number;
  clauses_consumed: number;
  clauses_remaining: number;
  coverage_pct: number;
  complete: boolean;
}

export interface RemainderResult {
  stats: ExtractionStats;
  remainder: Clause[];
}

export function computeRemainder(clauses: Clause[], traces: Trace[]): Clause[] {
  const tracedIds = new Set<string>();
  for (const trace of traces) {
    if (trace.clause_id) tracedIds.add(trace.clause_id);
    if (trace.clause_ids) {
      for (const id of trace.clause_ids) tracedIds.add(id);
    }
  }

  return clauses.filter(c => !tracedIds.has(c.clause_id));
}

export function isComplete(
  remainder: Clause[],
  previousRemainder: Clause[] | null = null,
): boolean {
  if (remainder.length === 0) return true;

  if (previousRemainder !== null) {
    if (remainder.length >= previousRemainder.length) return true;
  }

  return false;
}

export function extractionStats(
  clauses: Clause[],
  traces: Trace[],
  remainder: Clause[],
): ExtractionStats {
  return {
    total_clauses: clauses.length,
    traces_extracted: traces.length,
    clauses_consumed: clauses.length - remainder.length,
    clauses_remaining: remainder.length,
    coverage_pct: clauses.length > 0
      ? (clauses.length - remainder.length) / clauses.length * 100
      : 0,
    complete: remainder.length === 0,
  };
}
