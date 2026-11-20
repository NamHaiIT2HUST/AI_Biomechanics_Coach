"""Exploratory baseline using uncertain visual drafts; NOT a validated benchmark.

This does not mark annotations as reviewed and uses no test split. A missing pose
causes a reported failure under the existing strict landmark analyzer.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.core.landmark_analysis import analyze_landmarks
from app.core.pose import PoseEngine
from app.core.rep_validation import evaluate_dataset
from rep_annotation_tasks import PREPARED, DEFAULT_OUTPUT, sha256_file, validate_tasks


def summarize(tasks, records, tolerance_s=0.2):
    """Compare successful runs only; failures are listed, never turned into zeros."""
    task_map = {task['id']: task for task in tasks['videos']}
    grouped = {'train': [], 'validation': []}
    failures = []
    for record in records:
        task = task_map[record['id']]
        if record['status'] != 'ok':
            failures.append({'id': record['id'], 'split': task['split'], 'error': record['error']})
            continue
        grouped[task['split']].append({
            'id': task['id'], 'fps': task['fps'],
            'reference_bottom_frames': [rep['bottom_frame'] for rep in task['reps']],
            'predicted_bottom_frames': record['bottom_frames'],
        })
    return {
        'interpretation': 'Exploratory comparison against uncertain AI visual drafts; not ground truth or independent human evaluation.',
        'tolerance_s': tolerance_s, 'attempted': len(records),
        'successful': sum(len(v) for v in grouped.values()), 'failures': failures,
        'by_split': {split: evaluate_dataset(videos, tolerance_s) for split, videos in grouped.items()},
    }


def write_json(path, data):
    # Write only to a fresh run directory, never overwrite user annotations.
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tasks', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--min-duration', type=float, default=1.0)
    parser.add_argument('--bottom-threshold', type=float, default=150.0)
    parser.add_argument('--tolerance', type=float, default=0.2)
    args = parser.parse_args()
    tasks = json.loads(args.tasks.read_text(encoding='utf8'))
    validate_tasks(tasks)
    if not tasks['videos'] or any(t['annotation_status'] != 'needs_review' or not t['reps'] for t in tasks['videos']):
        raise ValueError('Expected explicitly uncertain drafts with candidate reps for every video')
    if args.output_dir.exists():
        raise FileExistsError(f'Run directory already exists: {args.output_dir}')
    args.output_dir.mkdir(parents=True)
    write_json(args.output_dir / 'references_snapshot.json', tasks)
    write_json(args.output_dir / 'configuration.json', {'min_duration_s': args.min_duration,
        'bottom_threshold': args.bottom_threshold, 'tolerance_s': args.tolerance,
        'note': 'Results are tentative: reference drafts need independent review.'})
    records = []
    engine = PoseEngine()
    for index, task in enumerate(tasks['videos'], 1):
        started = time.monotonic()
        print(f'[{index}/{len(tasks["videos"])}] {task["id"]}', flush=True)
        try:
            path = (PREPARED / task['video_path']).resolve()
            if not path.is_relative_to(PREPARED.resolve()) or not path.is_file() or sha256_file(path) != task['video_sha256']:
                raise ValueError('Missing, unsafe, or changed input video')
            extraction = engine.extract_from_video(str(path))
            if extraction.total_frames != task['frame_count'] or abs(extraction.fps - task['fps']) > 0.01:
                raise ValueError('Video metadata does not match the reference task')
            pose = asdict(extraction)
            write_json(args.output_dir / f'{task["id"]}_pose.json', pose)
            analysis = analyze_landmarks(pose, min_duration_s=args.min_duration, bottom_threshold=args.bottom_threshold)
            record = {'id': task['id'], 'status': 'ok', 'detection_rate': extraction.detection_rate,
                      'low_visibility_frames': analysis['low_visibility_frames'],
                      'bottom_frames': [rep['bottom_frame'] for rep in analysis['reps']],
                      'duration_s': round(time.monotonic() - started, 2)}
        except Exception as exc:
            record = {'id': task['id'], 'status': 'failed', 'error': f'{type(exc).__name__}: {exc}',
                      'duration_s': round(time.monotonic() - started, 2)}
        records.append(record)
        write_json(args.output_dir / 'records.json', records)
        print(' ', record['status'], record.get('error', ''), 'seconds', record['duration_s'], flush=True)
    summary = summarize(tasks, records, args.tolerance)
    write_json(args.output_dir / 'summary.json', summary)
    print(json.dumps({'successful': summary['successful'], 'attempted': summary['attempted'],
                      'failures': len(summary['failures'])}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
