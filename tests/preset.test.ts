import { describe, it, expect } from 'vitest';
import { resolve } from 'node:path';
import { loadPreset, validatePreset, resolvePreset, listPresets } from '../src/preset.js';

const PKG_ROOT = resolve(import.meta.dirname, '..');

describe('preset', () => {
  describe('loadPreset', () => {
    it('loads built-in spec-coverage preset', () => {
      const preset = loadPreset('spec-coverage', PKG_ROOT);
      expect(preset.name).toBe('spec-coverage');
      expect(preset.trace_types).toEqual(['REQUIREMENT', 'DECISION', 'WISH', 'OPEN_QUESTION', 'EXCLUSION']);
      expect(preset.coverage_statuses).toEqual(['COVERED', 'PARTIAL', 'MISSING', 'DEFERRED', 'N/A']);
      expect(preset.prompts.extract).toBe('extract.txt');
      expect(preset.prompts.coverage_check).toBe('coverage_check.txt');
      expect(preset.prompts.reverse_check).toBe('reverse_check.txt');
    });

    it('throws for missing preset', () => {
      expect(() => loadPreset('nonexistent', PKG_ROOT)).toThrow('Preset "nonexistent" not found');
    });
  });

  describe('validatePreset', () => {
    it('accepts valid preset', () => {
      const valid = {
        name: 'test',
        trace_types: ['A', 'B'],
        coverage_statuses: ['X', 'Y'],
        prompts: { extract: 'extract.txt' },
      };
      expect(validatePreset(valid)).toEqual(valid);
    });

    it('rejects missing required field', () => {
      expect(() => validatePreset({ name: 'test', trace_types: ['A'] }))
        .toThrow('missing required field: coverage_statuses');
    });

    it('rejects non-object', () => {
      expect(() => validatePreset(null)).toThrow('must be a JSON object');
      expect(() => validatePreset([])).toThrow('must be a JSON object');
    });

    it('rejects invalid trace_types', () => {
      expect(() => validatePreset({
        name: 'test',
        trace_types: 'not-array',
        coverage_statuses: ['X'],
        prompts: {},
      })).toThrow('"trace_types" must be a string array');
    });
  });

  describe('resolvePreset', () => {
    it('finds built-in preset', () => {
      const path = resolvePreset('spec-coverage', PKG_ROOT);
      expect(path).toBe(resolve(PKG_ROOT, 'presets', 'spec-coverage.json'));
    });

    it('returns null for missing preset', () => {
      expect(resolvePreset('nonexistent', PKG_ROOT)).toBeNull();
    });
  });

  describe('listPresets', () => {
    it('lists available presets', () => {
      const presets = listPresets(PKG_ROOT);
      expect(presets.length).toBeGreaterThan(0);
      const specCoverage = presets.find(p => p.name === 'spec-coverage');
      expect(specCoverage).toBeDefined();
      expect(specCoverage!.description).toContain('coverage');
    });
  });
});
