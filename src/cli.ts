#!/usr/bin/env node

import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadPreset, listPresets } from './preset.js';
import type { Preset } from './preset.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PKG_ROOT = resolve(__dirname, '..');

const DEFAULT_PRESET = 'spec-coverage';

function loadJson(path: string): unknown {
  return JSON.parse(readFileSync(path, 'utf-8'));
}

function getVersion(): string {
  const pkg = loadJson(resolve(PKG_ROOT, 'package.json')) as { version: string };
  return pkg.version;
}

function printUsage(): void {
  const cmds = [
    'split', 'extract-prompt', 'extract-validate', 'remainder',
    'match-prompt', 'match-validate',
    'reverse-extract-validate', 'reverse-match-prompt', 'reverse-match-validate',
    'finalize', 'status', 'delta',
    'presets', 'init', 'update',
  ];
  process.stderr.write(`set-trace v${getVersion()} — claim traceability tool\n\n`);
  process.stderr.write(`Usage: set-trace <command> [--preset <name>] [args...]\n\n`);
  process.stderr.write(`Commands:\n`);
  for (const c of cmds) {
    process.stderr.write(`  ${c}\n`);
  }
  process.exit(1);
}

function extractPresetArg(args: string[]): { presetName: string; remaining: string[] } {
  const remaining: string[] = [];
  let presetName = DEFAULT_PRESET;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--preset' && args[i + 1]) {
      presetName = args[++i];
    } else {
      remaining.push(args[i]);
    }
  }
  return { presetName, remaining };
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    printUsage();
  }

  if (args[0] === '--version' || args[0] === '-V') {
    process.stdout.write(getVersion() + '\n');
    return;
  }

  const cmd = args[0];
  const cmdArgs = args.slice(1);
  const { presetName, remaining } = extractPresetArg(cmdArgs);

  let preset: Preset | undefined;
  function getPreset(): Preset {
    if (!preset) preset = loadPreset(presetName, PKG_ROOT);
    return preset;
  }

  switch (cmd) {
    case 'split': {
      const { cmdSplit } = await import('./commands/split.js');
      await cmdSplit(remaining);
      break;
    }
    case 'extract-prompt': {
      const { cmdExtractPrompt } = await import('./commands/extract-prompt.js');
      await cmdExtractPrompt(remaining, PKG_ROOT, getPreset());
      break;
    }
    case 'extract-validate': {
      const { cmdExtractValidate } = await import('./commands/extract-validate.js');
      await cmdExtractValidate(remaining, getPreset());
      break;
    }
    case 'remainder': {
      const { cmdRemainder } = await import('./commands/remainder.js');
      await cmdRemainder(remaining);
      break;
    }
    case 'match-prompt': {
      const { cmdMatchPrompt } = await import('./commands/match-prompt.js');
      await cmdMatchPrompt(remaining, PKG_ROOT, getPreset());
      break;
    }
    case 'match-validate': {
      const { cmdMatchValidate } = await import('./commands/match-validate.js');
      await cmdMatchValidate(remaining, getPreset());
      break;
    }
    case 'reverse-extract-validate': {
      const { cmdReverseExtractValidate } = await import('./commands/reverse-extract-validate.js');
      await cmdReverseExtractValidate(remaining);
      break;
    }
    case 'reverse-match-prompt': {
      const { cmdReverseMatchPrompt } = await import('./commands/reverse-match-prompt.js');
      await cmdReverseMatchPrompt(remaining, PKG_ROOT, getPreset());
      break;
    }
    case 'reverse-match-validate': {
      const { cmdReverseMatchValidate } = await import('./commands/reverse-match-validate.js');
      await cmdReverseMatchValidate(remaining);
      break;
    }
    case 'finalize': {
      const { cmdFinalize } = await import('./commands/finalize.js');
      await cmdFinalize(remaining);
      break;
    }
    case 'status': {
      const { cmdStatus } = await import('./commands/status.js');
      await cmdStatus(remaining);
      break;
    }
    case 'delta': {
      const { cmdDelta } = await import('./commands/delta.js');
      await cmdDelta(remaining);
      break;
    }
    case 'presets': {
      const { cmdPresets } = await import('./commands/presets.js');
      await cmdPresets(PKG_ROOT);
      break;
    }
    case 'init': {
      const { cmdInit } = await import('./commands/init.js');
      await cmdInit(remaining, PKG_ROOT);
      break;
    }
    case 'update': {
      const { cmdUpdate } = await import('./commands/update.js');
      await cmdUpdate(remaining, PKG_ROOT);
      break;
    }
    default:
      process.stderr.write(`Unknown command: ${cmd}\n`);
      printUsage();
  }
}

main().catch((err: unknown) => {
  process.stderr.write(`Error: ${err instanceof Error ? err.message : String(err)}\n`);
  process.exit(1);
});
