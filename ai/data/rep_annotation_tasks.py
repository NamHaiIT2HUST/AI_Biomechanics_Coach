"""Create and validate independent manual squat annotation tasks.

No detector output is read. Paths in task files are relative to prepared_squat.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREPARED = ROOT / 'data/external/prepared_squat'
DEFAULT_OUTPUT = ROOT / 'data/external/annotation_work/tasks.json'
SUBJECTS = {
    'train': ('subject_003', 'subject_004', 'subject_005'),
    'validation': ('subject_002', 'subject_009'),
}


def sha256_file(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def build_tasks(rows, base):
    """Select fixed side-view tasks from development splits only."""
    tasks = []
    for split, subjects in SUBJECTS.items():
        for subject in subjects:
            for quality in ('good', 'bad'):
                candidates = [r for r in rows if r['dataset'] == 'multiview' and r['split'] == split
                              and r['subject'] == subject and r['view'] == 'side'
                              and r['video_label'] == quality]
                if len(candidates) != 1:
                    raise ValueError(f'Expected exactly one video for {split}/{subject}/{quality}')
                row = candidates[0]
                path = (base / row['path']).resolve()
                if not path.is_relative_to(base.resolve()) or not path.is_file():
                    raise ValueError(f'Invalid or missing source file: {row["path"]}')
                tasks.append({
                    'id': Path(row['path']).stem, 'dataset': 'multiview', 'subject': subject,
                    'split': split, 'view': 'side', 'video_label': quality,
                    'video_path': row['path'], 'video_sha256': sha256_file(path),
                    'fps': row['fps'], 'frame_count': row['frames'],
                    'annotation_status': 'unreviewed', 'annotator': None,
                    'label_protocol': 'manual_video_only_v1', 'reps': [], 'notes': '',
                })
    return {'schema_version': 1, 'description': 'Development only; no test subjects.', 'videos': tasks}


def validate_tasks(data, *, require_complete=False, allow_test=False):
    """Validate reviewed reference marks. Empty list means zero reps only if reviewed."""
    if data.get('schema_version') != 1 or not isinstance(data.get('videos'), list):
        raise ValueError('Invalid annotation schema')
    ids = set()
    for video in data['videos']:
        vid = video.get('id')
        if not isinstance(vid, str) or not vid or vid in ids:
            raise ValueError('Missing or duplicate video id')
        ids.add(vid)
        allowed_splits = ('train', 'validation', 'test') if allow_test else ('train', 'validation')
        if video.get('split') not in allowed_splits:
            raise ValueError(f'{vid}: test and unassigned videos are not development tasks')
        status = video.get('annotation_status')
        if status not in ('unreviewed', 'reviewed', 'needs_review'):
            raise ValueError(f'{vid}: invalid annotation status')
        if require_complete and status != 'reviewed':
            raise ValueError(f'{vid}: annotation is not reviewed')
        if status == 'reviewed' and not str(video.get('annotator') or '').strip():
            raise ValueError(f'{vid}: reviewed video needs an annotator')
        n, fps = video.get('frame_count'), video.get('fps')
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0 or not isinstance(fps, (int, float)) or isinstance(fps, bool) or not math.isfinite(fps) or fps <= 0:
            raise ValueError(f'{vid}: invalid frame count or FPS')
        reps = video.get('reps')
        if not isinstance(reps, list):
            raise ValueError(f'{vid}: reps must be a list')
        previous_end = -1
        for rep in reps:
            marks = [rep.get(k) for k in ('start_frame', 'bottom_frame', 'end_frame')]
            if any(isinstance(x, bool) or not isinstance(x, int) for x in marks):
                raise ValueError(f'{vid}: frames must be integers')
            start, bottom, end = marks
            if not (0 <= start <= bottom <= end < n) or start <= previous_end:
                raise ValueError(f'{vid}: invalid or overlapping rep boundaries')
            previous_end = end
    return len(ids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    create = subs.add_parser('create')
    create.add_argument('--manifest', type=Path, default=PREPARED / 'multiview_manifest.jsonl')
    create.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    check = subs.add_parser('validate')
    check.add_argument('file', type=Path)
    check.add_argument('--require-complete', action='store_true')
    check.add_argument('--allow-test', action='store_true', help='Explicitly validate held-out test tasks')
    args = parser.parse_args()
    if args.command == 'create':
        if args.output.exists():
            raise FileExistsError(f'Will not overwrite existing annotations: {args.output}')
        rows = [json.loads(line) for line in args.manifest.read_text(encoding='utf8').splitlines() if line.strip()]
        data = build_tasks(rows, PREPARED)
        validate_tasks(data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        print(f'Created {len(data["videos"])} unreviewed video tasks: {args.output}')
    else:
        data = json.loads(args.file.read_text(encoding='utf8'))
        count = validate_tasks(data, require_complete=args.require_complete, allow_test=args.allow_test)
        remaining = sum(v['annotation_status'] != 'reviewed' for v in data['videos'])
        print(f'Validated {count} tasks; {remaining} still need review.')


if __name__ == '__main__':
    main()
