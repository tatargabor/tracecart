#!/usr/bin/env node

import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PKG_ROOT = resolve(__dirname, '..');

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
    'init', 'update',
  ];
  process.stderr.write(`set-trace v${getVersion()} — claim traceability tool\n\n`);
  process.stderr.write(`Usage: set-trace <command> [args...]\n\n`);
  process.stderr.write(`Commands:\n`);
  for (const c of cmds) {
    process.stderr.write(`  ${c}\n`);
  }
  process.exit(1);
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

  switch (cmd) {
    case 'split': {
      const { cmdSplit } = await import('./commands/split.js');
      await cmdSplit(cmdArgs);
      break;
    }
    case 'extract-prompt': {
      const { cmdExtractPrompt } = await import('./commands/extract-prompt.js');
      await cmdExtractPrompt(cmdArgs, PKG_ROOT);
      break;
    }
    case 'extract-validate': {
      const { cmdExtractValidate } = await import('./commands/extract-validate.js');
      await cmdExtractValidate(cmdArgs);
      break;
    }
    case 'remainder': {
      const { cmdRemainder } = await import('./commands/remainder.js');
      await cmdRemainder(cmdArgs);
      break;
    }
    case 'match-prompt': {
      const { cmdMatchPrompt } = await import('./commands/match-prompt.js');
      await cmdMatchPrompt(cmdArgs, PKG_ROOT);
      break;
    }
    case 'match-validate': {
      const { cmdMatchValidate } = await import('./commands/match-validate.js');
      await cmdMatchValidate(cmdArgs);
      break;
    }
    case 'reverse-extract-validate': {
      const { cmdReverseExtractValidate } = await import('./commands/reverse-extract-validate.js');
      await cmdReverseExtractValidate(cmdArgs);
      break;
    }
    case 'reverse-match-prompt': {
      const { cmdReverseMatchPrompt } = await import('./commands/reverse-match-prompt.js');
      await cmdReverseMatchPrompt(cmdArgs, PKG_ROOT);
      break;
    }
    case 'reverse-match-validate': {
      const { cmdReverseMatchValidate } = await import('./commands/reverse-match-validate.js');
      await cmdReverseMatchValidate(cmdArgs);
      break;
    }
    case 'finalize': {
      const { cmdFinalize } = await import('./commands/finalize.js');
      await cmdFinalize(cmdArgs);
      break;
    }
    case 'status': {
      const { cmdStatus } = await import('./commands/status.js');
      await cmdStatus(cmdArgs);
      break;
    }
    case 'delta': {
      const { cmdDelta } = await import('./commands/delta.js');
      await cmdDelta(cmdArgs);
      break;
    }
    case 'init': {
      const { cmdInit } = await import('./commands/init.js');
      await cmdInit(cmdArgs, PKG_ROOT);
      break;
    }
    case 'update': {
      const { cmdUpdate } = await import('./commands/update.js');
      await cmdUpdate(cmdArgs, PKG_ROOT);
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
