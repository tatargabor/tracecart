import { readFileSync } from 'node:fs';
import { formatPrompt, batchTraces } from '../match/coverage.js';

export async function cmdMatchPrompt(args: string[], _pkgRoot: string): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: set-trace match-prompt <traces.json> <target.md> [--lang hu|en] [--exclusions <text>]\n');
    process.exit(1);
  }

  const tracesData = JSON.parse(readFileSync(args[0], 'utf-8'));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const traces: any[] = tracesData.traces ?? (Array.isArray(tracesData) ? tracesData : []);
  const targetText = readFileSync(args[1], 'utf-8');

  let lang = 'hu';
  let exclusions = '';
  for (let i = 2; i < args.length; i++) {
    if (args[i] === '--lang' && args[i + 1]) { lang = args[++i]; }
    else if (args[i] === '--exclusions' && args[i + 1]) { exclusions = args[++i]; }
  }

  const batches = batchTraces(traces);
  if (batches.length === 1) {
    process.stdout.write(formatPrompt(traces, targetText, exclusions, lang));
  } else {
    for (let bi = 0; bi < batches.length; bi++) {
      process.stderr.write(`--- BATCH ${bi + 1}/${batches.length} ---\n`);
      process.stdout.write(formatPrompt(batches[bi], targetText, exclusions, lang));
      if (bi < batches.length - 1) {
        process.stdout.write('\n---BATCH_SEPARATOR---\n');
      }
    }
  }
}
