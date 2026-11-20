"""Prepare source-preserving squat subsets; no model training or inferred labels.

Run: python ai/data/prepare_squat_datasets.py
Outputs live under data/external/prepared_squat and remain outside Git.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import random
import re
import shutil
import zlib
import zipfile

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = ROOT / 'data' / 'external'
OUTPUT = EXTERNAL / 'prepared_squat'
MULTI_SHA256 = '6d927246dbd2ed8a314b41201c94ebdcbd1b4abec0851d1ca39f82afda8a5eed'
MULTI_PATTERN = re.compile(r'^Dataset Exercise-wise/squat/(good|bad)/(side|front|diagonal)/(subject_\d+)_squat_\1_\2\.mp4$')
CF_PATTERN = re.compile(r'^CFRep-main/CFRep/(squat_(diag|front|side)_([mw]\d+)_(\d+)_(\d+))\.mp4$')
UI_PATTERN = re.compile(r'^(?:Segmented Movements|Incorrect Segmented Movements)/(Kinect|Vicon)/(Angles|Positions)/(m01_(s\d+)_e\d+_(?:angles|positions)(?:_inc)?\.txt)$')


def digest(path, algorithm):
    with path.open('rb') as file:
        return hashlib.file_digest(file, algorithm).hexdigest()


def group_splits(subjects, seed=20261120):
    """Deterministic disjoint subject groups within one dataset, not across datasets."""
    subjects = sorted(set(subjects))
    random.Random(seed).shuffle(subjects)
    if len(subjects) < 3:
        raise ValueError('Need at least three distinct subjects for train/val/test')
    n_test = max(1, round(len(subjects) * .15))
    n_val = max(1, round(len(subjects) * .15))
    return {subject: ('test' if i < n_test else 'validation' if i < n_test + n_val else 'train')
            for i, subject in enumerate(subjects)}


def extract_entry(archive, member, target):
    """Allow only explicitly constructed destinations and preserve conflicting files."""
    base = OUTPUT.resolve()
    destination = (base / target).resolve()
    if not destination.is_relative_to(base):
        raise ValueError(f'Unsafe path: {target}')
    info = archive.getinfo(member)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        crc = 0
        with destination.open('rb') as file:
            while block := file.read(1024 * 1024):
                crc = zlib.crc32(block, crc)
        if destination.stat().st_size == info.file_size and crc == info.CRC:
            return destination
        raise FileExistsError(f'Existing file differs; not overwritten: {destination}')
    temporary = destination.with_name(destination.name + '.preparing')
    if temporary.exists():
        raise FileExistsError(f'Incomplete file already exists: {temporary}')
    try:
        with archive.open(info) as source, temporary.open('xb') as out:
            shutil.copyfileobj(source, out, 1024 * 1024)
        temporary.rename(destination)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return destination


def prepare_multiview():
    path = EXTERNAL / 'multiview_fitness' / 'exercise_wise.zip'
    if digest(path, 'sha256') != MULTI_SHA256:
        raise ValueError('Multi-View archive SHA-256 mismatch')
    rows = []
    with zipfile.ZipFile(path) as z:
        matches = [(n, MULTI_PATTERN.fullmatch(n)) for n in z.namelist()]
        matches = [(n, m) for n, m in matches if m]
        splits = group_splits(m.group(3) for _, m in matches)
        for member, match in matches:
            quality, view, subject = match.groups()
            target = Path('multiview') / quality / view / PurePosixPath(member).name
            extract_entry(z, member, target)
            rows.append({'dataset': 'multiview', 'subject': subject, 'split': splits[subject], 'view': view,
                         'video_label': quality, 'label_scope': 'video', 'path': target.as_posix(),
                         'license': 'CC-BY-4.0', 'source_member': member})
    return rows


def prepare_cfrep():
    rows = []
    path = EXTERNAL / 'cfrep' / 'cfrep-main.zip'
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        for member in names:
            match = CF_PATTERN.fullmatch(member)
            if not match:
                continue
            stem, view, subject, valid, invalid = match.groups()
            json_prefix = f'CFRep-main/CFRep/json_keypoints/squat/{stem}/'
            annotations = sorted(n for n in names if n.startswith(json_prefix) and n.endswith('.json'))
            if not annotations:
                raise ValueError(f'No annotations for {stem}')
            # Existing source pose estimates are not MediaPipe ground truth.
            label_doc = json.loads(z.read(annotations[0]))
            segments = label_doc.get('annotations')
            if not isinstance(segments, list):
                raise ValueError(f'Missing source annotations: {stem}')
            segment_counts = Counter(segment.get('label') for segment in segments)
            if segment_counts['rep'] != int(valid) or segment_counts['no-rep'] != int(invalid):
                raise ValueError(f'CFRep annotation counts do not match filename: {stem}')
            target = Path('cfrep') / 'videos' / f'{stem}.mp4'
            label_target = Path('cfrep') / 'annotations' / f'{stem}.json'
            extract_entry(z, member, target)
            extract_entry(z, annotations[0], label_target)
            rows.append({'dataset': 'cfrep', 'subject': subject, 'split': 'unassigned', 'view': view,
                         'video_label': None, 'label_scope': 'source_rep_intervals', 'path': target.as_posix(),
                         'annotation_path': label_target.as_posix(), 'source_valid_count': int(valid),
                         'source_invalid_count': int(invalid), 'annotation_intervals': len(segments),
                         'license': 'unknown_review_required', 'subject_identity_review': subject == 'm32',
                         'source_member': member})
    return rows


def prepare_ui():
    metadata = json.loads((EXTERNAL / 'ui_prmd' / 'zenodo_metadata.json').read_text(encoding='utf8'))
    expected = {entry['key']: entry['checksum'].split(':', 1)[1] for entry in metadata['files']}
    sources = [('correct', 'Segmented Movements.zip'), ('incorrect', 'Incorrect Segmented Movements.zip')]
    selected = []
    for quality, filename in sources:
        path = EXTERNAL / 'ui_prmd' / filename
        if digest(path, 'md5') != expected[filename]:
            raise ValueError(f'UI-PRMD checksum mismatch: {filename}')
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                m = UI_PATTERN.fullmatch(name)
                if m:
                    selected.append((quality, filename, name, m.groups()))
    splits = group_splits(groups[3] for _, _, _, groups in selected)
    rows = []
    for quality, filename in sources:
        with zipfile.ZipFile(EXTERNAL / 'ui_prmd' / filename) as z:
            for label, archive_name, member, groups in selected:
                if archive_name != filename:
                    continue
                sensor, measure, basename, subject = groups
                target = Path('ui_prmd') / quality / sensor / measure / basename
                extract_entry(z, member, target)
                rows.append({'dataset': 'ui_prmd', 'subject': subject, 'split': splits[subject], 'view': None,
                             'label': label, 'label_scope': 'segmented_recording', 'sensor': sensor,
                             'measurement': measure, 'path': target.as_posix(), 'license': 'PDDL-1.0',
                             'source_member': member})
    return rows


def main():
    import cv2
    OUTPUT.mkdir(parents=True, exist_ok=True)
    all_rows = prepare_multiview() + prepare_cfrep() + prepare_ui()
    # Check that extracted MP4 metadata is readable; do not invent rep labels.
    bad_videos = []
    for row in all_rows:
        if not row['path'].endswith('.mp4'):
            continue
        cap = cv2.VideoCapture(str(OUTPUT / row['path']))
        ok, frame = cap.read()
        fps = cap.get(cv2.CAP_PROP_FPS)
        count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        if not ok or fps <= 0 or count <= 0:
            bad_videos.append(row['path'])
        else:
            row.update(fps=round(fps, 4), frames=int(count), width=int(frame.shape[1]), height=int(frame.shape[0]))
    if bad_videos:
        raise ValueError(f'Videos could not be read: {bad_videos}')
    for dataset in ('multiview', 'cfrep', 'ui_prmd'):
        rows = [row for row in all_rows if row['dataset'] == dataset]
        target = OUTPUT / f'{dataset}_manifest.jsonl'
        target.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf8')
        print(dataset, 'records', len(rows), 'splits', dict(Counter(row['split'] for row in rows)))
    print('Prepared output:', OUTPUT)
    print('CFRep split remains unassigned pending licence and participant identity review.')


if __name__ == '__main__':
    main()
