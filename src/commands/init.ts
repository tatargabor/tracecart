import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const TEMPLATE_REL = 'templates/claude/commands/set/trace.md';
const TARGET_REL = '.claude/commands/set/trace.md';

function extractVersion(content: string): string | null {
  const m = content.match(/<!--\s*set-trace\s+v([\d.]+)\s*-->/);
  return m ? m[1] : null;
}

export async function cmdInit(args: string[], pkgRoot: string): Promise<void> {
  const projectDir = args[0] || process.cwd();
  const templatePath = resolve(pkgRoot, TEMPLATE_REL);
  const targetPath = resolve(projectDir, TARGET_REL);

  if (!existsSync(templatePath)) {
    process.stderr.write(`Error: template not found at ${templatePath}\n`);
    process.exit(1);
  }

  const template = readFileSync(templatePath, 'utf-8');
  const templateVersion = extractVersion(template);

  if (existsSync(targetPath)) {
    const existing = readFileSync(targetPath, 'utf-8');
    const existingVersion = extractVersion(existing);

    if (existingVersion === templateVersion) {
      process.stderr.write(`Already up to date (v${templateVersion})\n`);
      return;
    }

    process.stderr.write(`Updating ${TARGET_REL}: v${existingVersion ?? '?'} → v${templateVersion}\n`);
  }

  const targetDir = resolve(projectDir, '.claude/commands/set');
  mkdirSync(targetDir, { recursive: true });
  writeFileSync(targetPath, template, 'utf-8');
  process.stderr.write(`Created ${TARGET_REL}\n`);
}
