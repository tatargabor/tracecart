import { listPresets } from '../preset.js';

export async function cmdPresets(pkgRoot: string): Promise<void> {
  const presets = listPresets(pkgRoot);

  if (presets.length === 0) {
    process.stderr.write('No presets found.\n');
    return;
  }

  for (const p of presets) {
    const source = p.source === 'project-local' ? ' [local]' : '';
    const desc = p.description ? ` — ${p.description}` : '';
    process.stdout.write(`${p.name}${source}${desc}\n`);
  }
}
