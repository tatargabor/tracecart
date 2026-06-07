import { readFileSync } from 'node:fs';
import { processDocument } from '../parse/clause-split.js';

export async function cmdSplit(args: string[]): Promise<void> {
  if (!args[0]) {
    process.stderr.write('Usage: set-trace split <source.md> [--lang hu|en]\n');
    process.exit(1);
  }

  const sourcePath = args[0];
  const text = readFileSync(sourcePath, 'utf-8');
  const clauses = processDocument(text);

  const contentClauses = clauses.filter(c => !c.is_header);
  const compoundLines = new Set<number>();
  for (const c of contentClauses) {
    if (c.clause_index > 0) compoundLines.add(c.line_number);
  }

  const result = {
    source_file: sourcePath,
    total_lines: text.split('\n').length,
    content_clauses: contentClauses.length,
    compound_lines_split: compoundLines.size,
    clauses,
  };

  process.stdout.write(JSON.stringify(result, null, 2));
}
