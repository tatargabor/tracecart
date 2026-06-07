import { readFileSync } from 'node:fs';
import { validateMatches } from '../match/coverage.js';
import type { Preset } from '../preset.js';

export async function cmdMatchValidate(args: string[], preset: Preset): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: tracecart match-validate <llm_output.txt> <traces.json> [--preset <name>]\n');
    process.exit(1);
  }

  const rawOutput = readFileSync(args[0], 'utf-8');
  const tracesData = JSON.parse(readFileSync(args[1], 'utf-8'));
  const traces = tracesData.traces ?? (Array.isArray(tracesData) ? tracesData : []);

  const validStatuses = new Set(preset.coverage_statuses.map(s => s.toUpperCase()));
  const result = validateMatches(rawOutput, traces, validStatuses);
  process.stdout.write(JSON.stringify(result, null, 2));
}
