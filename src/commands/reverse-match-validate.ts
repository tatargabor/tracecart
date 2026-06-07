import { readFileSync } from 'node:fs';
import { validateReverseMatches } from '../match/coverage.js';

export async function cmdReverseMatchValidate(args: string[]): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: set-trace reverse-match-validate <llm_output.txt> <reverse_traces.json>\n');
    process.exit(1);
  }

  const rawOutput = readFileSync(args[0], 'utf-8');
  const reverseData = JSON.parse(readFileSync(args[1], 'utf-8'));
  const reverseTraces = reverseData.traces ?? (Array.isArray(reverseData) ? reverseData : []);

  const result = validateReverseMatches(rawOutput, reverseTraces);
  process.stdout.write(JSON.stringify(result, null, 2));
}
