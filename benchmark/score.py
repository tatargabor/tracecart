#!/usr/bin/env python3
"""Score extraction methods against ground truth.

Metrics:
- Detection recall: % of GT items represented in ANY extracted item (even merged)
- Atomic recall: % of GT items with their OWN dedicated extracted item
- Precision: % of extracted items that map to at least one GT item
- Difficulty breakdown: recall by difficulty category (explicit/implicit/compound/nuance)
- F1: harmonic mean of atomic recall and precision

Usage:
  python3 score.py ground-truth.json method-a.json [method-b.json ...]

Method files must have a "requirements" array with "id" and "gt_mapping" fields.
gt_mapping: list of GT IDs this item covers (e.g., ["GT-001"] or ["GT-023", "GT-024"] if merged)
"""

import json
import sys
from pathlib import Path


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def score_method(gt: list[dict], method: dict) -> dict:
    """Score a method against ground truth."""
    gt_ids = {r['id'] for r in gt}
    gt_by_id = {r['id']: r for r in gt}

    extracted = method.get('requirements', [])
    method_name = method.get('name', '?')

    covered_gt_ids = set()
    atomic_gt_ids = set()
    mapped_count = 0

    for item in extracted:
        mapping = item.get('gt_mapping', [])
        if mapping:
            mapped_count += 1
            covered_gt_ids.update(mapping)
            if len(mapping) == 1:
                atomic_gt_ids.update(mapping)

    missing_gt = gt_ids - covered_gt_ids

    detection_recall = len(covered_gt_ids) / len(gt_ids) if gt_ids else 0
    atomic_recall = len(atomic_gt_ids) / len(gt_ids) if gt_ids else 0
    precision = mapped_count / len(extracted) if extracted else 0
    f1_atomic = 2 * (atomic_recall * precision) / (atomic_recall + precision) if (atomic_recall + precision) > 0 else 0

    difficulty_stats = {}
    for r in gt:
        d = r.get('difficulty', 'unknown')
        if d not in difficulty_stats:
            difficulty_stats[d] = {'total': 0, 'detected': 0, 'atomic': 0}
        difficulty_stats[d]['total'] += 1
        if r['id'] in covered_gt_ids:
            difficulty_stats[d]['detected'] += 1
        if r['id'] in atomic_gt_ids:
            difficulty_stats[d]['atomic'] += 1

    return {
        'name': method_name,
        'extracted_count': len(extracted),
        'gt_count': len(gt_ids),
        'detection_recall': detection_recall,
        'atomic_recall': atomic_recall,
        'precision': precision,
        'f1_atomic': f1_atomic,
        'missing': sorted(missing_gt),
        'missing_details': [
            {'id': gid, 'text': gt_by_id[gid]['text'][:60], 'difficulty': gt_by_id[gid].get('difficulty', '?')}
            for gid in sorted(missing_gt)
        ],
        'difficulty': {
            k: {
                'total': v['total'],
                'detection_recall': v['detected'] / v['total'] if v['total'] > 0 else 0,
                'atomic_recall': v['atomic'] / v['total'] if v['total'] > 0 else 0,
            }
            for k, v in difficulty_stats.items()
        },
    }


def print_comparison(scores: list[dict]):
    """Print a comparison table."""
    print("=" * 90)
    print("BENCHMARK RESULTS — Chapter 9: Rendeléskezelés")
    print("=" * 90)
    print(f"\nGround truth: {scores[0]['gt_count']} atomic requirements\n")

    header = f"{'Method':<30s} {'Items':>5s} {'Det.Recall':>10s} {'Atom.Recall':>11s} {'Precision':>9s} {'F1':>6s}"
    print(header)
    print("-" * len(header))

    for s in scores:
        print(f"{s['name']:<30s} {s['extracted_count']:>5d} {s['detection_recall']:>9.0%} {s['atomic_recall']:>10.0%} {s['precision']:>9.0%} {s['f1_atomic']:>5.0%}")

    print(f"\n{'Difficulty breakdown':}")
    print(f"{'':30s} {'explicit':>10s} {'compound':>10s} {'implicit':>10s} {'nuance':>10s}")
    print("-" * 70)

    for s in scores:
        parts = []
        for d in ['explicit', 'compound', 'implicit', 'nuance']:
            if d in s['difficulty']:
                parts.append(f"{s['difficulty'][d]['atomic_recall']:>9.0%}")
            else:
                parts.append(f"{'—':>10s}")
        print(f"{s['name']:<30s} {''.join(parts)}")

    best = max(scores, key=lambda s: s['f1_atomic'])
    print(f"\n🏆 Best method: {best['name']} (F1={best['f1_atomic']:.0%})")

    if best['missing']:
        print(f"\nEven the best method missed {len(best['missing'])} items:")
        for m in best['missing_details']:
            print(f"  - {m['id']} [{m['difficulty']}]: {m['text']}...")

    print()


def main():
    if len(sys.argv) < 3:
        print("Usage: score.py ground-truth.json method-a.json [method-b.json ...]", file=sys.stderr)
        sys.exit(1)

    gt_data = load_json(sys.argv[1])
    gt = gt_data['requirements']

    scores = []
    for method_path in sys.argv[2:]:
        method_data = load_json(method_path)
        score = score_method(gt, method_data)
        scores.append(score)

    print_comparison(scores)

    json.dump(scores, open('/tmp/set-trace-benchmark-results.json', 'w'), ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
