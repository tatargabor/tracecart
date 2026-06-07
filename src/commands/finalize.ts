import { readFileSync, writeFileSync } from 'node:fs';
import { applyMatches, resolveRefs } from '../match/coverage.js';
import { buildTraceMap } from '../output/trace-map.js';

export async function cmdFinalize(args: string[]): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: set-trace finalize <traces.json> <matches.json> --source <file> --target <file> [--output trace-map.json]\n');
    process.exit(1);
  }

  const tracesData = JSON.parse(readFileSync(args[0], 'utf-8'));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const traces: any[] = tracesData.traces ?? (Array.isArray(tracesData) ? tracesData : []);
  const matchesData = JSON.parse(readFileSync(args[1], 'utf-8'));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const matches: any[] = matchesData.matches ?? (Array.isArray(matchesData) ? matchesData : []);

  const sourceFiles: string[] = [];
  const targetFiles: string[] = [];
  let outputPath: string | null = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let untraced: any[] = [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let reverseTraces: any[] | null = null;

  let i = 2;
  while (i < args.length) {
    if (args[i] === '--source' && args[i + 1]) { sourceFiles.push(args[++i]); }
    else if (args[i] === '--target' && args[i + 1]) { targetFiles.push(args[++i]); }
    else if (args[i] === '--output' && args[i + 1]) { outputPath = args[++i]; }
    else if (args[i] === '--untraced' && args[i + 1]) {
      const ud = JSON.parse(readFileSync(args[++i], 'utf-8'));
      untraced = ud.remainder ?? (Array.isArray(ud) ? ud : []);
    }
    else if (args[i] === '--reverse-traces' && args[i + 1]) {
      const rd = JSON.parse(readFileSync(args[++i], 'utf-8'));
      reverseTraces = rd.traces ?? (Array.isArray(rd) ? rd : []);
    }
    i++;
  }

  const matchedTraces = applyMatches(traces, matches);
  const resolvedTraces = resolveRefs(matchedTraces, targetFiles);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const traceMap = buildTraceMap(resolvedTraces as any[], sourceFiles, targetFiles, untraced, undefined, (reverseTraces ?? undefined) as any);

  const outputJson = JSON.stringify(traceMap, null, 2);

  if (outputPath) {
    writeFileSync(outputPath, outputJson, 'utf-8');
    process.stderr.write(`Written to ${outputPath}\n`);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const summary: any = traceMap.summary;
    process.stderr.write(
      `Forward coverage: ${summary.coverage_score_pct}% ` +
      `(${summary.covered}C/${summary.partial}P/${summary.missing}M/${summary.deferred}D)\n`
    );
    if ('reverse_total' in summary) {
      process.stderr.write(
        `Reverse coverage: ${summary.reverse_coverage_pct}% ` +
        `(${summary.reverse_traced}T/${summary.reverse_partial_source ?? 0}P/${summary.reverse_untraced}U)\n`
      );
    }
  } else {
    process.stdout.write(outputJson);
  }
}
