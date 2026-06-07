import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { batchTraces } from '../match/coverage.js';
import type { Preset } from '../preset.js';

export async function cmdMatchPrompt(args: string[], pkgRoot: string, preset: Preset): Promise<void> {
  if (args.length < 2) {
    process.stderr.write('Usage: set-trace match-prompt <traces.json> <target.md> [--exclusions <text>] [--preset <name>]\n');
    process.exit(1);
  }

  const tracesData = JSON.parse(readFileSync(args[0], 'utf-8'));
  const traces: Record<string, unknown>[] = tracesData.traces ?? (Array.isArray(tracesData) ? tracesData : []);
  const targetText = readFileSync(args[1], 'utf-8');

  let exclusions = '';
  for (let i = 2; i < args.length; i++) {
    if (args[i] === '--exclusions' && args[i + 1]) { exclusions = args[++i]; }
  }

  const templateFile = preset.prompts.coverage_check ?? 'coverage_check.txt';
  const templatePath = resolve(pkgRoot, 'prompts', templateFile);
  const template = readFileSync(templatePath, 'utf-8');

  function formatPromptFromPreset(batch: Record<string, unknown>[]): string {
    const reqLines: string[] = [];
    for (const t of batch) {
      const tid = (t.id ?? t.sentence_id ?? '') as string;
      const text = (t.text ?? '') as string;
      const ttype = (t.type ?? 'REQUIREMENT') as string;
      const implicit = t.implicit ? ' [implicit]' : '';
      reqLines.push(`[${tid}] (${ttype}${implicit}) ${text}`);
    }

    let prompt = template.replace('{requirements}', reqLines.join('\n'));
    prompt = prompt.replace('{specs}', targetText);
    prompt = prompt.replace('{exclusions}', exclusions || '(none specified)');
    prompt = prompt.replace('{trace_types}', preset.trace_types.join(' | '));
    prompt = prompt.replace('{coverage_statuses}', preset.coverage_statuses.join(' | '));
    return prompt;
  }

  const batches = batchTraces(traces);
  if (batches.length === 1) {
    process.stdout.write(formatPromptFromPreset(traces));
  } else {
    for (let bi = 0; bi < batches.length; bi++) {
      process.stderr.write(`--- BATCH ${bi + 1}/${batches.length} ---\n`);
      process.stdout.write(formatPromptFromPreset(batches[bi]));
      if (bi < batches.length - 1) {
        process.stdout.write('\n---BATCH_SEPARATOR---\n');
      }
    }
  }
}
