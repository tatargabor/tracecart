import { readFileSync } from 'node:fs';
import { validateMatches } from '../match/coverage.js';

export async function cmdMatchValidate(args: string[]): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: set-trace match-validate <llm_output.txt> <traces.json>\n');
    process.exit(1);
  }

  const rawOutput = readFileSync(args[0], 'utf-8');
  const tracesData = JSON.parse(readFileSync(args[1], 'utf-8'));
  const traces = tracesData.traces ?? (Array.isArray(tracesData) ? tracesData : []);

  const result = validateMatches(rawOutput, traces);
  process.stdout.write(JSON.stringify(result, null, 2));
}
