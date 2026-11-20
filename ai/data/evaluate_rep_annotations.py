"""Evaluate detector predictions against reviewed manual labels, keeping splits separate.

Prediction JSON: {"videos": [{"id": "video id", "bottom_frames": [42, 90]}]}.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.core.rep_validation import evaluate_dataset
from rep_annotation_tasks import validate_tasks


def evaluate_annotations(reference, predictions, tolerance_s=0.2):
    validate_tasks(reference, require_complete=True)
    if not reference['videos']:
        raise ValueError('No reviewed reference videos')
    if not isinstance(predictions.get('videos'), list):
        raise ValueError('Invalid predictions schema')
    prediction_map = {}
    for item in predictions['videos']:
        vid = item.get('id')
        if not isinstance(vid, str) or not vid or vid in prediction_map:
            raise ValueError('Missing or duplicate prediction video id')
        if not isinstance(item.get('bottom_frames'), list):
            raise ValueError(f'{vid}: bottom_frames must be a list')
        prediction_map[vid] = item['bottom_frames']
    reference_ids = {v['id'] for v in reference['videos']}
    if reference_ids != set(prediction_map):
        raise ValueError('Prediction and reference video IDs must match exactly')
    split_records = {'train': [], 'validation': []}
    for video in reference['videos']:
        frames = prediction_map[video['id']]
        if any(isinstance(f, bool) or not isinstance(f, int) or f < 0 or f >= video['frame_count'] for f in frames):
            raise ValueError(f'{video["id"]}: predicted frame out of bounds')
        split_records[video['split']].append({
            'id': video['id'], 'fps': video['fps'],
            'reference_bottom_frames': [rep['bottom_frame'] for rep in video['reps']],
            'predicted_bottom_frames': frames,
        })
    return {split: evaluate_dataset(videos, tolerance_s) for split, videos in split_records.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('references', type=Path)
    parser.add_argument('predictions', type=Path)
    parser.add_argument('--tolerance', type=float, default=0.2)
    args = parser.parse_args()
    references = json.loads(args.references.read_text(encoding='utf8'))
    predictions = json.loads(args.predictions.read_text(encoding='utf8'))
    print(json.dumps(evaluate_annotations(references, predictions, args.tolerance), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
