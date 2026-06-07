interface TraceEntry {
  id: string;
  text?: string;
  status?: string;
}

interface TraceMap {
  traces?: TraceEntry[];
  summary?: {
    coverage_score_pct?: number;
    reverse_coverage_pct?: number;
  };
}

interface DeltaItem {
  id: string;
  text: string;
  old_status: string;
  new_status: string;
}

interface NewOrRemovedItem {
  id: string;
  text: string;
  status: string;
}

interface DeltaSummary {
  old_coverage_pct: number;
  new_coverage_pct: number;
  coverage_diff: number;
  improved_count: number;
  regressed_count: number;
  new_count: number;
  removed_count: number;
  unchanged_count: number;
  old_reverse_pct?: number;
  new_reverse_pct?: number;
  reverse_diff?: number;
}

export interface DeltaResult {
  summary: DeltaSummary;
  improved: DeltaItem[];
  regressed: DeltaItem[];
  new: NewOrRemovedItem[];
  removed: NewOrRemovedItem[];
}

function _buildIndex(traces: TraceEntry[]): [Map<string, TraceEntry>, Map<string, TraceEntry>] {
  const byId = new Map<string, TraceEntry>();
  const byText = new Map<string, TraceEntry>();
  for (const t of traces) {
    byId.set(t.id, t);
    const text = (t.text ?? '').trim().toLowerCase();
    if (text) {
      byText.set(text, t);
    }
  }
  return [byId, byText];
}

const RANK: Record<string, number> = {
  'COVERED': 3, 'TRACED': 3,
  'PARTIAL': 2, 'PARTIAL_SOURCE': 2, 'DEFERRED': 2,
  'MISSING': 1, 'UNTRACED_IN_SOURCE': 1,
  'N/A': 0,
};

export function compare(oldMap: TraceMap, newMap: TraceMap): DeltaResult {
  const oldTraces = oldMap.traces ?? [];
  const newTraces = newMap.traces ?? [];

  const [oldById, oldByText] = _buildIndex(oldTraces);
  const [, newByText] = _buildIndex(newTraces);

  const improved: DeltaItem[] = [];
  const regressed: DeltaItem[] = [];
  const unchanged: string[] = [];
  const newItems: NewOrRemovedItem[] = [];
  const removed: NewOrRemovedItem[] = [];

  const matchedOld = new Set<string>();

  for (const t of newTraces) {
    const tid = t.id;
    let oldT = oldById.get(tid);

    if (!oldT) {
      const text = (t.text ?? '').trim().toLowerCase();
      oldT = oldByText.get(text);
    }

    if (oldT) {
      matchedOld.add(oldT.id);
      const oldStatus = oldT.status ?? 'MISSING';
      const newStatus = t.status ?? 'MISSING';
      const oldRank = RANK[oldStatus] ?? 0;
      const newRank = RANK[newStatus] ?? 0;

      if (newRank > oldRank) {
        improved.push({
          id: tid, text: t.text ?? '',
          old_status: oldStatus, new_status: newStatus,
        });
      } else if (newRank < oldRank) {
        regressed.push({
          id: tid, text: t.text ?? '',
          old_status: oldStatus, new_status: newStatus,
        });
      } else {
        unchanged.push(tid);
      }
    } else {
      newItems.push({
        id: tid, text: t.text ?? '',
        status: t.status ?? 'MISSING',
      });
    }
  }

  for (const t of oldTraces) {
    if (!matchedOld.has(t.id)) {
      const text = (t.text ?? '').trim().toLowerCase();
      if (!newByText.has(text)) {
        removed.push({
          id: t.id, text: t.text ?? '',
          status: t.status ?? 'MISSING',
        });
      }
    }
  }

  const oldSummary = oldMap.summary ?? {};
  const newSummary = newMap.summary ?? {};
  const oldPct = oldSummary.coverage_score_pct ?? 0;
  const newPct = newSummary.coverage_score_pct ?? 0;

  const summary: DeltaSummary = {
    old_coverage_pct: oldPct,
    new_coverage_pct: newPct,
    coverage_diff: Math.round((newPct - oldPct) * 10) / 10,
    improved_count: improved.length,
    regressed_count: regressed.length,
    new_count: newItems.length,
    removed_count: removed.length,
    unchanged_count: unchanged.length,
  };

  if ('reverse_coverage_pct' in oldSummary || 'reverse_coverage_pct' in newSummary) {
    const oldRev = oldSummary.reverse_coverage_pct ?? 0;
    const newRev = newSummary.reverse_coverage_pct ?? 0;
    summary.old_reverse_pct = oldRev;
    summary.new_reverse_pct = newRev;
    summary.reverse_diff = Math.round((newRev - oldRev) * 10) / 10;
  }

  return {
    summary,
    improved,
    regressed,
    new: newItems,
    removed,
  };
}

export function formatText(delta: DeltaResult): string {
  const s = delta.summary;
  const lines: string[] = [];

  const diffStr = s.coverage_diff >= 0 ? `+${s.coverage_diff}` : String(s.coverage_diff);
  lines.push(`Forward: ${s.old_coverage_pct}% → ${s.new_coverage_pct}% (${diffStr}%)`);

  if (s.old_reverse_pct !== undefined) {
    const revDiff = s.reverse_diff! >= 0 ? `+${s.reverse_diff}` : String(s.reverse_diff);
    lines.push(`Reverse: ${s.old_reverse_pct}% → ${s.new_reverse_pct}% (${revDiff}%)`);
  }

  lines.push('');

  if (delta.improved.length > 0) {
    lines.push(`IMPROVED (${delta.improved.length}):`);
    for (const item of delta.improved) {
      lines.push(`  ▲ ${item.id}  ${item.old_status} → ${item.new_status}`);
      lines.push(`    ${item.text}`);
    }
    lines.push('');
  }

  if (delta.regressed.length > 0) {
    lines.push(`REGRESSED (${delta.regressed.length}):`);
    for (const item of delta.regressed) {
      lines.push(`  ▼ ${item.id}  ${item.old_status} → ${item.new_status}`);
      lines.push(`    ${item.text}`);
    }
    lines.push('');
  }

  if (delta.new.length > 0) {
    lines.push(`NEW (${delta.new.length}):`);
    for (const item of delta.new) {
      lines.push(`  + ${item.id}  [${item.status}]`);
      lines.push(`    ${item.text}`);
    }
    lines.push('');
  }

  if (delta.removed.length > 0) {
    lines.push(`REMOVED (${delta.removed.length}):`);
    for (const item of delta.removed) {
      lines.push(`  - ${item.id}  [${item.status}]`);
      lines.push(`    ${item.text}`);
    }
    lines.push('');
  }

  if (delta.improved.length === 0 && delta.regressed.length === 0 &&
      delta.new.length === 0 && delta.removed.length === 0) {
    lines.push('No changes.');
  }

  lines.push(`Unchanged: ${s.unchanged_count} traces`);

  return lines.join('\n');
}
