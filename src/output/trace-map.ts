export const TRACE_MAP_VERSION = 1;

interface TraceSource {
  file?: string;
  line?: number;
  col_start?: number;
  col_end?: number;
}

interface TraceRef {
  file?: string;
  section?: string;
  line?: number;
}

interface TraceInput {
  id?: string;
  text?: string;
  type?: string;
  source?: TraceSource;
  status?: string;
  refs?: TraceRef[];
  topics?: string[];
  nearest_source_trace?: string;
  similarity_note?: string;
  [key: string]: unknown;
}

interface UntracedClause {
  clause_id: string;
  text: string;
}

interface AnnotationRange {
  start: { line: number; col: number };
  end: { line: number; col: number };
}

export interface SourceAnnotation {
  range: AnnotationRange;
  status: string;
  trace_id: string | undefined;
  trace_text: string;
  refs: unknown[];
}

export interface TargetAnnotation {
  line: number;
  section: string;
  trace_id: string | undefined;
  trace_text: string;
  status: string;
  source?: TraceSource | Record<string, unknown>;
  nearest_source_trace?: string;
  similarity_note?: string;
}

export interface Summary {
  total: number;
  covered: number;
  partial: number;
  missing: number;
  deferred: number;
  superseded: number;
  na: number;
  coverage_score_pct: number;
  reverse_total?: number;
  reverse_traced?: number;
  reverse_partial_source?: number;
  reverse_untraced?: number;
  reverse_coverage_pct?: number;
}

export interface TraceMap {
  version: number;
  generated: string;
  source_files: string[];
  target_files: string[];
  traces: TraceInput[];
  untraced_clauses: UntracedClause[];
  summary: Summary;
  reverse_traces?: TraceInput[];
  metadata?: Record<string, unknown>;
}

export function buildTraceMap(
  traces: TraceInput[],
  sourceFiles: string[],
  targetFiles: string[],
  untracedClauses: Array<{ clause_id?: string; text?: string }> | null = null,
  metadata: Record<string, unknown> | null = null,
  reverseTraces: TraceInput[] | null = null,
): TraceMap {
  const summary = computeSummary(traces, reverseTraces);

  const traceMap: TraceMap = {
    version: TRACE_MAP_VERSION,
    generated: new Date().toISOString(),
    source_files: sourceFiles,
    target_files: targetFiles,
    traces,
    untraced_clauses: (untracedClauses ?? []).map(c => ({
      clause_id: c.clause_id ?? '',
      text: c.text ?? '',
    })),
    summary,
  };

  if (reverseTraces !== null) {
    traceMap.reverse_traces = reverseTraces;
  }

  if (metadata) {
    traceMap.metadata = metadata;
  }

  return traceMap;
}

export function computeSummary(
  traces: TraceInput[],
  reverseTraces: TraceInput[] | null = null,
): Summary {
  const statusCounts: Record<string, number> = {};
  for (const trace of traces) {
    const status = trace.status ?? 'UNKNOWN';
    statusCounts[status] = (statusCounts[status] ?? 0) + 1;
  }

  const total = traces.length;
  const covered = statusCounts['COVERED'] ?? 0;
  const partial = statusCounts['PARTIAL'] ?? 0;
  const missing = statusCounts['MISSING'] ?? 0;

  const checkable = covered + partial + missing;
  const score = checkable > 0
    ? (covered + partial * 0.5) / checkable * 100
    : 0;

  const summary: Summary = {
    total,
    covered,
    partial,
    missing,
    deferred: statusCounts['DEFERRED'] ?? 0,
    superseded: statusCounts['SUPERSEDED'] ?? 0,
    na: statusCounts['N/A'] ?? 0,
    coverage_score_pct: Math.round(score * 10) / 10,
  };

  if (reverseTraces !== null) {
    const revCounts: Record<string, number> = {};
    for (const rt of reverseTraces) {
      const st = rt.status ?? 'UNKNOWN';
      revCounts[st] = (revCounts[st] ?? 0) + 1;
    }

    const revTraced = revCounts['TRACED'] ?? 0;
    const revPartial = revCounts['PARTIAL_SOURCE'] ?? 0;
    const revUntraced = revCounts['UNTRACED_IN_SOURCE'] ?? 0;
    const revCheckable = revTraced + revPartial + revUntraced;

    const revScore = revCheckable > 0
      ? (revTraced + revPartial * 0.5) / revCheckable * 100
      : 0;

    summary.reverse_total = reverseTraces.length;
    summary.reverse_traced = revTraced;
    summary.reverse_partial_source = revPartial;
    summary.reverse_untraced = revUntraced;
    summary.reverse_coverage_pct = Math.round(revScore * 10) / 10;
  }

  return summary;
}

export function buildSourceAnnotations(traces: TraceInput[]): Record<string, SourceAnnotation[]> {
  const annotations: Record<string, SourceAnnotation[]> = {};

  for (const trace of traces) {
    const source = trace.source;
    const filepath = source?.file;
    if (!filepath) continue;

    if (!annotations[filepath]) {
      annotations[filepath] = [];
    }

    annotations[filepath].push({
      range: {
        start: { line: source.line ?? 0, col: source.col_start ?? 0 },
        end: { line: source.line ?? 0, col: source.col_end ?? 0 },
      },
      status: trace.status ?? 'UNKNOWN',
      trace_id: trace.id,
      trace_text: trace.text ?? '',
      refs: trace.refs ?? [],
    });
  }

  return annotations;
}

export function buildTargetAnnotations(
  traces: TraceInput[],
  reverseTraces: TraceInput[] | null = null,
): Record<string, TargetAnnotation[]> {
  const annotations: Record<string, TargetAnnotation[]> = {};

  for (const trace of traces) {
    for (const ref of (trace.refs ?? [])) {
      const filepath = ref.file;
      if (!filepath) continue;

      if (!annotations[filepath]) {
        annotations[filepath] = [];
      }

      annotations[filepath].push({
        line: ref.line ?? 0,
        section: ref.section ?? '',
        trace_id: trace.id,
        trace_text: trace.text ?? '',
        status: trace.status ?? 'UNKNOWN',
        source: trace.source ?? {},
      });
    }
  }

  for (const rt of (reverseTraces ?? [])) {
    if (rt.status !== 'UNTRACED_IN_SOURCE' && rt.status !== 'PARTIAL_SOURCE') {
      continue;
    }

    const source = rt.source;
    const filepath = source?.file;
    if (!filepath) continue;

    if (!annotations[filepath]) {
      annotations[filepath] = [];
    }

    annotations[filepath].push({
      line: source.line ?? 0,
      section: '',
      trace_id: rt.id,
      trace_text: rt.text ?? '',
      status: rt.status!,
      nearest_source_trace: rt.nearest_source_trace,
      similarity_note: rt.similarity_note ?? '',
    });
  }

  return annotations;
}
