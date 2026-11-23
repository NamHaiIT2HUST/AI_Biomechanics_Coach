"""Compare rep-duration thresholds on cached TRAIN poses and provisional labels.

This is exploratory development, not a benchmark or model training. Partial
videos are shown for inspection but excluded from aggregate matching metrics.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.core.partial_landmark_analysis import analyze_detected_spans
from app.core.rep_validation import evaluate_dataset
from rep_annotation_tasks import validate_tasks


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def sweep(reference, pose_dir, durations, *, tolerance=0.2):
    validate_tasks(reference)
    if not durations or any(not math.isfinite(d) or d <= 0 for d in durations) or len(set(durations)) != len(durations):
        raise ValueError('Durations must be unique, positive and finite')
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Tolerance must be nonnegative and finite')
    tasks = [v for v in reference['videos'] if v['split'] == 'train']
    if not tasks:
        raise ValueError('No train videos')
    results = {str(d): {'complete': [], 'videos': []} for d in durations}
    inputs = []
    for task in tasks:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', task['id']):
            raise ValueError('Unsafe video id')
        path = pose_dir / f'{task["id"]}_pose.json'
        if not path.is_file():
            for group in results.values():
                group['videos'].append({'id': task['id'], 'status': 'failed', 'error': 'Cached pose missing'})
            continue
        try:
            pose = json.loads(path.read_text(encoding='utf8'))
            if len(pose['frames']) != task['frame_count'] or abs(float(pose['fps']) - task['fps']) > 0.01:
                raise ValueError('Cached pose metadata differs from annotation')
            inputs.append({'id': task['id'], 'pose_sha256': sha256_file(path), 'annotation_status': task['annotation_status']})
            for duration in durations:
                analysis = analyze_detected_spans(pose, min_duration_s=duration)
                predicted = [r['bottom_frame'] for r in analysis['reps']]
                entry = {'id': task['id'], 'status': analysis['status'], 'missing_frames': analysis['missing_frames'],
                         'draft_rep_count': len(task['reps']), 'predicted_bottom_frames': predicted}
                group = results[str(duration)]
                group['videos'].append(entry)
                if analysis['status'] == 'complete':
                    group['complete'].append({'id': task['id'], 'fps': task['fps'],
                        'reference_bottom_frames': [r['bottom_frame'] for r in task['reps']],
                        'predicted_bottom_frames': predicted})
        except (ValueError, KeyError, TypeError, OSError) as exc:
            for group in results.values():
                if not any(v['id'] == task['id'] for v in group['videos']):
                    group['videos'].append({'id': task['id'], 'status': 'failed', 'error': str(exc)})
    for group in results.values():
        group['complete_only'] = evaluate_dataset(group.pop('complete'), tolerance)
    return {'interpretation': 'TRAIN only; provisional AI annotations are not independent ground truth. Partial videos are excluded from aggregate matching metrics.',
            'parameters': {'durations_s': durations, 'bottom_threshold': 150.0, 'standing_threshold': 160.0,
                           'prominence': 15.0, 'tolerance_s': tolerance},
            'inputs': inputs, 'results': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--durations', type=float, nargs='+', default=[0.7, 0.8, 0.9, 1.0, 1.2])
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f'Will not overwrite: {args.output}')
    reference_path = args.run_dir / 'references_snapshot.json'
    reference = json.loads(reference_path.read_text(encoding='utf8'))
    result = sweep(reference, args.run_dir, args.durations)
    result['reference_sha256'] = sha256_file(reference_path)
    with args.output.open('x', encoding='utf8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(f'Wrote exploratory TRAIN sweep to {args.output}')


if __name__ == '__main__':
    main()
