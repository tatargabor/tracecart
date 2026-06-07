import { readFileSync } from 'node:fs';
import { formatPrompt } from '../extract/extract.js';
import type { Clause } from '../extract/extract.js';

function parseArgs(args: string[]): { clausesPath: string; lang: string; sourceFile: string } {
  let lang = 'hu';
  let sourceFile = '';
  const clausesPath = args[0];

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--lang' && args[i + 1]) { lang = args[++i]; }
    else if (args[i] === '--source' && args[i + 1]) { sourceFile = args[++i]; }
  }

  return { clausesPath, lang, sourceFile };
}

export async function cmdExtractPrompt(args: string[], pkgRoot: string): Promise<void> {
  if (!args[0]) {
    process.stderr.write('Usage: set-trace extract-prompt <clauses.json> [--lang hu|en] [--source <file>]\n');
    process.exit(1);
  }

  const { clausesPath, lang, sourceFile } = parseArgs(args);
  const data = JSON.parse(readFileSync(clausesPath, 'utf-8'));
  const clauses: Clause[] = data.clauses ?? (Array.isArray(data) ? data : []);

  const prompt = formatPrompt(clauses, sourceFile, lang, pkgRoot);
  process.stdout.write(prompt);
}
