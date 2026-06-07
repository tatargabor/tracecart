import { readFileSync } from 'node:fs';
import { computeRemainder, extractionStats } from '../extract/remainder.js';
import { computeSummary } from '../output/trace-map.js';

export async function cmdStatus(args: string[]): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: tracecart status <traces.json> <clauses.json>\n');
    process.exit(1);
  }

  const tracesData = JSON.parse(readFileSync(args[0], 'utf-8'));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const traces: any[] = tracesData.traces ?? (Array.isArray(tracesData) ? tracesData : []);
  const clausesData = JSON.parse(readFileSync(args[1], 'utf-8'));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const clauses: any[] = clausesData.clauses ?? (Array.isArray(clausesData) ? clausesData : []);

  const contentClauses = clauses.filter((c: any) => !c.is_header);
  const remainder = computeRemainder(contentClauses, traces);
  const stats = extractionStats(contentClauses, traces, remainder);

  const hasStatus = traces.some((t: any) => 'status' in t);

  process.stderr.write(`Clauses: ${stats.total_clauses}\n`);
  process.stderr.write(`Traces extracted: ${stats.traces_extracted}\n`);
  process.stderr.write(`Clauses consumed: ${stats.clauses_consumed}/${stats.total_clauses} (${stats.coverage_pct.toFixed(1)}%)\n`);
  process.stderr.write(`Remainder: ${stats.clauses_remaining} clauses\n`);
  process.stderr.write(`Extraction complete: ${stats.complete}\n`);

  if (hasStatus) {
    const summary = computeSummary(traces);
    process.stderr.write(`\nCoverage matching:\n`);
    process.stderr.write(`  Score: ${summary.coverage_score_pct}%\n`);
    process.stderr.write(`  COVERED: ${summary.covered}\n`);
    process.stderr.write(`  PARTIAL: ${summary.partial}\n`);
    process.stderr.write(`  MISSING: ${summary.missing}\n`);
    process.stderr.write(`  DEFERRED: ${summary.deferred}\n`);
  }
}
