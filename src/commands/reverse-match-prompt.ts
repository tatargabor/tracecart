import { readFileSync } from 'node:fs';
import { formatReversePrompt, batchTraces } from '../match/coverage.js';

export async function cmdReverseMatchPrompt(args: string[], _pkgRoot: string): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: set-trace reverse-match-prompt <reverse_traces.json> <source_traces.json> [--lang hu|en]\n');
    process.exit(1);
  }

  const reverseData = JSON.parse(readFileSync(args[0], 'utf-8'));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const reverseTraces: any[] = reverseData.traces ?? (Array.isArray(reverseData) ? reverseData : []);
  const sourceData = JSON.parse(readFileSync(args[1], 'utf-8'));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sourceTraces: any[] = sourceData.traces ?? (Array.isArray(sourceData) ? sourceData : []);

  let lang = 'hu';
  for (let i = 2; i < args.length; i++) {
    if (args[i] === '--lang' && args[i + 1]) { lang = args[++i]; }
  }

  const batches = batchTraces(reverseTraces);
  if (batches.length === 1) {
    process.stdout.write(formatReversePrompt(reverseTraces, sourceTraces, lang));
  } else {
    for (let bi = 0; bi < batches.length; bi++) {
      process.stderr.write(`--- BATCH ${bi + 1}/${batches.length} ---\n`);
      process.stdout.write(formatReversePrompt(batches[bi], sourceTraces, lang));
      if (bi < batches.length - 1) {
        process.stdout.write('\n---BATCH_SEPARATOR---\n');
      }
    }
  }
}
