"""Inventory the prepared Multi-View squat manifest without reading video content.

Test records are counted only for split integrity; no model, threshold or feature
is fitted or evaluated. Outputs should remain outside Git.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = ROOT / 'data' / 'external' / 'prepared_squat'
MODEL = ROOT / 'ai' / 'models' / 'pretrained' / 'pose_landmarker_heavy.task'
CONFIG = ROOT / 'backend' / 'app' / 'exercises' / 'squat.json'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def audit(rows, base):
    """Check grouping, paths and file presence; no content hashes or video decode."""
    errors, grouped, subject_splits = [], defaultdict(list), defaultdict(set)
    seen_paths, seen_combinations = set(), set()
    base = base.resolve()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append(f'row {index}: not an object')
            continue
        subject, split, view, label, rel = (row.get(k) for k in ('subject', 'split', 'view', 'video_label', 'path'))
        if (row.get('dataset') != 'multiview' or not isinstance(subject, str) or not subject.strip()
                or split not in ('train', 'validation', 'test') or view not in ('side', 'front', 'diagonal')
                or label not in ('good', 'bad') or row.get('label_scope') != 'video'
                or not isinstance(rel, str) or not rel):
            errors.append(f'row {index}: invalid required metadata')
            continue
        combination = (subject, view, label)
        if combination in seen_combinations:
            errors.append(f'row {index}: duplicate subject/view/label')
        seen_combinations.add(combination)
        if rel in seen_paths:
            errors.append(f'row {index}: duplicate path')
        seen_paths.add(rel)
        path = (base / rel).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            errors.append(f'row {index}: missing or unsafe video path')
        fps, frames = row.get('fps'), row.get('frames')
        if (isinstance(fps, bool) or not isinstance(fps, (float, int)) or not math.isfinite(fps) or fps <= 0
                or isinstance(frames, bool) or not isinstance(frames, int) or frames <= 0):
            errors.append(f'row {index}: invalid FPS/frame count')
        subject_splits[subject].add(split)
        grouped[(split, view)].append(row)
    for subject, splits in sorted(subject_splits.items()):
        if len(splits) != 1:
            errors.append(f'subject {subject}: occurs in multiple splits')
    if not rows:
        errors.append('manifest is empty')
    summary = {}
    for (split, view), items in sorted(grouped.items()):
        summary[f'{split}/{view}'] = {'videos': len(items), 'subjects': len({v['subject'] for v in items}),
                                      'labels': dict(sorted(Counter(v['video_label'] for v in items).items()))}
    return {'valid': not errors, 'errors': errors, 'total_videos': len(rows),
            'total_subjects': len(subject_splits), 'by_split_view': summary,
            'limitations': ['File presence and manifest metadata only; content hashes, decode, source labels and cross-dataset identities are not verified.',
                            'Test metadata is used only to check split integrity, not to tune or evaluate models.']}


def git_state():
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip())
        return {'commit': revision, 'working_tree_dirty': dirty}
    except (OSError, subprocess.CalledProcessError):
        return {'commit': None, 'working_tree_dirty': None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; choose a new path')
    manifest = args.base / 'multiview_manifest.jsonl'
    rows = [json.loads(line) for line in manifest.read_text(encoding='utf8').splitlines() if line.strip()]
    result = audit(rows, args.base)
    result['provenance'] = {'manifest_sha256': sha256(manifest),
                            'config_sha256': sha256(CONFIG),
                            'pose_model_sha256': sha256(MODEL) if MODEL.is_file() else None,
                            'pose_model_present': MODEL.is_file(),
                            'python': sys.version.split()[0], 'git': git_state()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({'valid': result['valid'], 'videos': result['total_videos'],
                      'subjects': result['total_subjects'], 'error_count': len(result['errors'])}))
    if not result['valid']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
