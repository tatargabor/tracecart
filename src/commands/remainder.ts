import { readFileSync } from 'node:fs';
import { computeRemainder, isComplete, extractionStats } from '../extract/remainder.js';
import type { Clause, Trace } from '../extract/extract.js';

export async function cmdRemainder(args: string[]): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: tracecart remainder <clauses.json> <traces.json>\n');
    process.exit(1);
  }

  const clausesData = JSON.parse(readFileSync(args[0], 'utf-8'));
  const clauses: Clause[] = (clausesData.clauses ?? (Array.isArray(clausesData) ? clausesData : []));

  const tracesData = JSON.parse(readFileSync(args[1], 'utf-8'));
  const traces: Trace[] = (tracesData.traces ?? (Array.isArray(tracesData) ? tracesData : []));

  const contentClauses = clauses.filter(c => !c.is_header);
  const remainder = computeRemainder(contentClauses, traces);
  const stats = extractionStats(contentClauses, traces, remainder);
  const complete = isComplete(remainder, null);

  const result = { stats, remainder, complete };
  process.stdout.write(JSON.stringify(result, null, 2));
}
