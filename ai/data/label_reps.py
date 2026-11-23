"""Manually label a development video, independently of detector predictions.

Keys: A/D previous/next, J/L jump 15 frames, S/B/E start/bottom/end,
U undo last completed rep, C clear in-progress marks, N save needs-review,
R save reviewed, Q quit without saving. Frames are zero based.
"""
import argparse
import json
import os
from pathlib import Path

import cv2
from rep_annotation_tasks import DEFAULT_OUTPUT, PREPARED, sha256_file, validate_tasks


def save_tasks(path, data, *, allow_test=False):
    validate_tasks(data, allow_test=allow_test)
    tmp = path.with_name(path.name + '.tmp')
    if tmp.exists():
        raise FileExistsError(f'Refusing to overwrite temporary file: {tmp}')
    try:
        with tmp.open('x', encoding='utf8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def label(tasks_path, video_id, annotator, *, allow_test=False):
    data = json.loads(tasks_path.read_text(encoding='utf8'))
    validate_tasks(data, allow_test=allow_test)
    matches = [v for v in data['videos'] if v['id'] == video_id]
    if len(matches) != 1:
        raise ValueError(f'Video not found: {video_id}')
    video = matches[0]
    path = (PREPARED / video['video_path']).resolve()
    if not path.is_relative_to(PREPARED.resolve()) or not path.is_file():
        raise ValueError('Missing or unsafe video path')
    if sha256_file(path) != video['video_sha256']:
        raise ValueError('Video checksum differs from annotation task')
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f'Cannot open {path}')
    reps = [dict(rep) for rep in video['reps']]
    pending = {}
    frame_idx = 0
    message = 'A/D frame; J/L +/-15; S/B/E marks; R reviewed; N review; Q quit'
    try:
        while True:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = capture.read()
            if not ok:
                raise ValueError(f'Cannot decode frame {frame_idx}')
            height, width = frame.shape[:2]
            scale = min(1.0, 950 / max(height, width))
            if scale < 1:
                frame = cv2.resize(frame, None, fx=scale, fy=scale)
            display = cv2.copyMakeBorder(frame, 0, 100, 0, 0, cv2.BORDER_CONSTANT, value=(20, 20, 20))
            y = display.shape[0] - 75
            for line in (f'{video_id} frame {frame_idx}/{video["frame_count"]-1}  reps {len(reps)}',
                         f'Pending: {pending}', message):
                cv2.putText(display, line[:140], (8, y), cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1, cv2.LINE_AA)
                y += 24
            cv2.imshow('Independent rep annotation', display)
            key = cv2.waitKey(0) & 0xff
            message = 'A/D frame; J/L +/-15; S/B/E marks; R reviewed; N review; Q quit'
            if key in (ord('q'), 27):
                return False
            if key == ord('a'): frame_idx = max(0, frame_idx - 1)
            elif key == ord('d'): frame_idx = min(video['frame_count'] - 1, frame_idx + 1)
            elif key == ord('j'): frame_idx = max(0, frame_idx - 15)
            elif key == ord('l'): frame_idx = min(video['frame_count'] - 1, frame_idx + 15)
            elif key == ord('c'): pending = {}
            elif key == ord('u'):
                if reps: reps.pop()
            elif key == ord('s'):
                if reps and frame_idx <= reps[-1]['end_frame']:
                    message = 'Start must follow previous end.'
                else: pending = {'start_frame': frame_idx}
            elif key == ord('b'):
                if 'start_frame' not in pending or frame_idx < pending['start_frame']:
                    message = 'Set start first; bottom must follow start.'
                else: pending['bottom_frame'] = frame_idx
            elif key == ord('e'):
                if 'bottom_frame' not in pending or frame_idx < pending['bottom_frame']:
                    message = 'Set bottom first; end must follow bottom.'
                else:
                    pending['end_frame'] = frame_idx
                    reps.append(pending)
                    pending = {}
            elif key in (ord('r'), ord('n')):
                if pending:
                    message = 'Finish or clear pending marks before saving.'
                    continue
                video['reps'] = reps
                video['annotator'] = annotator
                video['annotation_status'] = 'reviewed' if key == ord('r') else 'needs_review'
                save_tasks(tasks_path, data, allow_test=allow_test)
                return True
    finally:
        capture.release()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tasks', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--id', required=True)
    parser.add_argument('--annotator', required=True)
    parser.add_argument('--allow-test', action='store_true', help='Explicitly allow a held-out test annotation task')
    args = parser.parse_args()
    if not args.annotator.strip():
        parser.error('annotator must not be empty')
    print('Saved' if label(args.tasks, args.id, args.annotator, allow_test=args.allow_test) else 'Exited without saving')


if __name__ == '__main__':
    main()
