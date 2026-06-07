import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { batchTraces } from '../match/coverage.js';
import type { Preset } from '../preset.js';

export async function cmdReverseMatchPrompt(args: string[], pkgRoot: string, preset: Preset): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: tracecart reverse-match-prompt <reverse_traces.json> <source_traces.json> [--preset <name>]\n');
    process.exit(1);
  }

  const reverseData = JSON.parse(readFileSync(args[0], 'utf-8'));
  const reverseTraces: Record<string, unknown>[] = reverseData.traces ?? (Array.isArray(reverseData) ? reverseData : []);
  const sourceData = JSON.parse(readFileSync(args[1], 'utf-8'));
  const sourceTraces: Record<string, unknown>[] = sourceData.traces ?? (Array.isArray(sourceData) ? sourceData : []);

  const templateFile = preset.prompts.reverse_check ?? 'reverse_check.txt';
  const templatePath = resolve(pkgRoot, 'prompts', templateFile);
  const template = readFileSync(templatePath, 'utf-8');

  function formatFromPreset(batch: Record<string, unknown>[]): string {
    const claimLines: string[] = [];
    for (const t of batch) {
      const tid = (t.id ?? '') as string;
      const text = (t.text ?? '') as string;
      const ttype = (t.type ?? 'REQUIREMENT') as string;
      claimLines.push(`[${tid}] (${ttype}) ${text}`);
    }

    const evidenceLines: string[] = [];
    for (const t of sourceTraces) {
      const tid = (t.id ?? '') as string;
      const text = (t.text ?? '') as string;
      const ttype = (t.type ?? 'REQUIREMENT') as string;
      const implicit = t.implicit ? ' [implicit]' : '';
      evidenceLines.push(`[${tid}] (${ttype}${implicit}) ${text}`);
    }

    let prompt = template.replace('{claims}', claimLines.join('\n'));
    prompt = prompt.replace('{evidence}', evidenceLines.join('\n'));
    return prompt;
  }

  const batches = batchTraces(reverseTraces);
  if (batches.length === 1) {
    process.stdout.write(formatFromPreset(reverseTraces));
  } else {
    for (let bi = 0; bi < batches.length; bi++) {
      process.stderr.write(`--- BATCH ${bi + 1}/${batches.length} ---\n`);
      process.stdout.write(formatFromPreset(batches[bi]));
      if (bi < batches.length - 1) {
        process.stdout.write('\n---BATCH_SEPARATOR---\n');
      }
    }
  }
}
