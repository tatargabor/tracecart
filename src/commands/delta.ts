import { readFileSync } from 'node:fs';
import { compare, formatText } from '../output/delta.js';

export async function cmdDelta(args: string[]): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: tracecart delta <old.json> <new.json> [--json]\n');
    process.exit(1);
  }

  const oldMap = JSON.parse(readFileSync(args[0], 'utf-8'));
  const newMap = JSON.parse(readFileSync(args[1], 'utf-8'));
  const useJson = args.includes('--json');

  const delta = compare(oldMap, newMap);

  if (useJson) {
    process.stdout.write(JSON.stringify(delta, null, 2));
  } else {
    process.stdout.write(formatText(delta) + '\n');
  }
}
