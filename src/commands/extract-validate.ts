import { readFileSync } from 'node:fs';
import { validateTraces } from '../extract/extract.js';
import type { Clause } from '../extract/extract.js';

export async function cmdExtractValidate(args: string[]): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: set-trace extract-validate <llm_output.txt> <clauses.json> [--source <file>]\n');
    process.exit(1);
  }

  const rawOutput = readFileSync(args[0], 'utf-8');
  const data = JSON.parse(readFileSync(args[1], 'utf-8'));
  const clauses: Clause[] = data.clauses ?? (Array.isArray(data) ? data : []);

  let sourceFile = '';
  for (let i = 2; i < args.length; i++) {
    if (args[i] === '--source' && args[i + 1]) { sourceFile = args[++i]; }
  }

  const result = validateTraces(rawOutput, clauses, sourceFile);
  process.stdout.write(JSON.stringify(result, null, 2));
}
