import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

export interface Preset {
  name: string;
  description?: string;
  version?: string;
  trace_types: string[];
  coverage_statuses: string[];
  prompts: Record<string, string>;
  defaults?: Record<string, string>;
}

const REQUIRED_FIELDS = ['name', 'trace_types', 'coverage_statuses', 'prompts'] as const;

export function validatePreset(data: unknown): Preset {
  if (typeof data !== 'object' || data === null || Array.isArray(data)) {
    throw new Error('Preset must be a JSON object');
  }

  const obj = data as Record<string, unknown>;

  for (const field of REQUIRED_FIELDS) {
    if (!(field in obj)) {
      throw new Error(`Preset missing required field: ${field}`);
    }
  }

  if (typeof obj.name !== 'string') {
    throw new Error('Preset "name" must be a string');
  }
  if (!Array.isArray(obj.trace_types) || obj.trace_types.some((t: unknown) => typeof t !== 'string')) {
    throw new Error('Preset "trace_types" must be a string array');
  }
  if (!Array.isArray(obj.coverage_statuses) || obj.coverage_statuses.some((s: unknown) => typeof s !== 'string')) {
    throw new Error('Preset "coverage_statuses" must be a string array');
  }
  if (typeof obj.prompts !== 'object' || obj.prompts === null || Array.isArray(obj.prompts)) {
    throw new Error('Preset "prompts" must be an object');
  }

  return obj as unknown as Preset;
}

export function resolvePreset(name: string, pkgRoot: string): string | null {
  const localPath = resolve(process.cwd(), 'presets', `${name}.json`);
  if (existsSync(localPath)) return localPath;

  const builtinPath = resolve(pkgRoot, 'presets', `${name}.json`);
  if (existsSync(builtinPath)) return builtinPath;

  return null;
}

export function loadPreset(name: string, pkgRoot: string): Preset {
  const path = resolvePreset(name, pkgRoot);
  if (!path) {
    const available = listPresets(pkgRoot);
    const names = available.map(p => p.name).join(', ');
    throw new Error(`Preset "${name}" not found. Available: ${names}`);
  }

  const raw = JSON.parse(readFileSync(path, 'utf-8'));
  return validatePreset(raw);
}

export interface PresetInfo {
  name: string;
  description: string;
  source: 'built-in' | 'project-local';
}

export function listPresets(pkgRoot: string): PresetInfo[] {
  const presets = new Map<string, PresetInfo>();

  const builtinDir = resolve(pkgRoot, 'presets');
  if (existsSync(builtinDir)) {
    for (const file of readdirSync(builtinDir)) {
      if (!file.endsWith('.json')) continue;
      try {
        const data = JSON.parse(readFileSync(resolve(builtinDir, file), 'utf-8'));
        const preset = validatePreset(data);
        presets.set(preset.name, {
          name: preset.name,
          description: preset.description ?? '',
          source: 'built-in',
        });
      } catch { /* skip invalid */ }
    }
  }

  const localDir = resolve(process.cwd(), 'presets');
  if (existsSync(localDir)) {
    for (const file of readdirSync(localDir)) {
      if (!file.endsWith('.json')) continue;
      try {
        const data = JSON.parse(readFileSync(resolve(localDir, file), 'utf-8'));
        const preset = validatePreset(data);
        presets.set(preset.name, {
          name: preset.name,
          description: preset.description ?? '',
          source: 'project-local',
        });
      } catch { /* skip invalid */ }
    }
  }

  return [...presets.values()];
}
