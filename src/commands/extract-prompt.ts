import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { Clause } from '../extract/extract.js';
import type { Preset } from '../preset.js';

function parseArgs(args: string[]): { clausesPath: string; sourceFile: string } {
  let sourceFile = '';
  const clausesPath = args[0];

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--source' && args[i + 1]) { sourceFile = args[++i]; }
  }

  return { clausesPath, sourceFile };
}

export async function cmdExtractPrompt(args: string[], pkgRoot: string, preset: Preset): Promise<void> {
  if (!args[0]) {
    process.stderr.write('Usage: set-trace extract-prompt <clauses.json> [--source <file>] [--preset <name>]\n');
    process.exit(1);
  }

  const { clausesPath, sourceFile } = parseArgs(args);
  const data = JSON.parse(readFileSync(clausesPath, 'utf-8'));
  const clauses: Clause[] = data.clauses ?? (Array.isArray(data) ? data : []);

  const templateFile = preset.prompts.extract ?? 'extract.txt';
  const templatePath = resolve(pkgRoot, 'prompts', templateFile);
  const template = readFileSync(templatePath, 'utf-8');

  const clauseLines: string[] = [];
  for (const c of clauses) {
    if (c.is_header || c.is_meta) continue;
    clauseLines.push(`[${c.clause_id}] ${c.text}`);
  }

  let prompt = template.replace('{clauses}', clauseLines.join('\n'));
  prompt = prompt.replace('{trace_types}', preset.trace_types.join(' | '));
  prompt = prompt.replace('{coverage_statuses}', preset.coverage_statuses.join(' | '));

  process.stdout.write(prompt);
}
