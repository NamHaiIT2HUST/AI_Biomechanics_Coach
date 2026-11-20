"""Reanalyze cached poses with gap-aware spans; exploratory drafts only."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.core.partial_landmark_analysis import analyze_detected_spans
from app.core.rep_validation import evaluate_dataset
from rep_annotation_tasks import validate_tasks


def analyze_cached(reference, pose_folder, min_duration=1.0, bottom_threshold=150.0, tolerance=0.2):
    validate_tasks(reference)
    grouped = {'train': [], 'validation': []}
    videos = []
    for task in reference['videos']:
        pose_path = pose_folder / f'{task["id"]}_pose.json'
        if not pose_path.is_file():
            videos.append({'id': task['id'], 'split': task['split'], 'status': 'failed', 'error': 'Cached pose missing'})
            continue
        try:
            pose = json.loads(pose_path.read_text(encoding='utf8'))
            result = analyze_detected_spans(pose, min_duration_s=min_duration, bottom_threshold=bottom_threshold)
            reference_frames = [r['bottom_frame'] for r in task['reps']]
            predicted_frames = [r['bottom_frame'] for r in result['reps']]
            videos.append({'id': task['id'], 'split': task['split'], 'status': result['status'],
                'missing_frames': result['missing_frames'], 'total_frames': result['total_frames'],
                'analyzed_frames': result['analyzed_frames'], 'draft_rep_count': len(reference_frames),
                'predicted_rep_count': len(predicted_frames), 'bottom_frames': predicted_frames,
                'warning': result['warning']})
            if result['status'] == 'complete':
                grouped[task['split']].append({'id': task['id'], 'fps': task['fps'],
                    'reference_bottom_frames': reference_frames, 'predicted_bottom_frames': predicted_frames})
        except Exception as exc:
            videos.append({'id': task['id'], 'split': task['split'], 'status': 'failed', 'error': str(exc)})
    return {'interpretation': 'Draft AI visual annotations are unreviewed. Results are exploratory and do not measure verified accuracy. Metrics exclude incomplete pose videos.',
            'parameters': {'bottom_threshold': bottom_threshold, 'min_duration_s': min_duration, 'tolerance_s': tolerance},
            'videos': videos, 'complete_only': {k: evaluate_dataset(v, tolerance) for k, v in grouped.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f'Will not overwrite: {args.output}')
    reference = json.loads((args.run_dir / 'references_snapshot.json').read_text(encoding='utf8'))
    result = analyze_cached(reference, args.run_dir)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'videos': len(result['videos']), 'statuses': {s: sum(v['status'] == s for v in result['videos']) for s in ('complete','partial','failed')}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
