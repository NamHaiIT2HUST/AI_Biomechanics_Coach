"""Freeze provisional AI labels for development without representing them as human-reviewed."""
import argparse
import hashlib
import json
from pathlib import Path
from rep_annotation_tasks import validate_tasks


def freeze(data):
    validate_tasks(data)
    if not data['videos'] or any(v['annotation_status'] != 'needs_review' or not v['reps'] or
                                  v.get('review_provenance', {}).get('annotator_type') != 'AI'
                                  for v in data['videos']):
        raise ValueError('All videos must contain AI draft labels and explicit AI provenance')
    payload = dict(data)
    payload['snapshot'] = {
        'id': 'ai-provisional-v1', 'usage': 'development_only',
        'quality': 'unverified', 'independent_benchmark': False,
        'warning': 'AI visual estimates; possible missed/incorrect reps and incomplete video segments; annotator saw baseline before audit.',
    }
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    data = freeze(json.loads(raw))
    data['snapshot']['source_sha256'] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'Frozen {len(data["videos"])} AI-labelled development videos: {args.output}')
    print('Unverified: not an independent benchmark; original task statuses unchanged.')


if __name__ == '__main__':
    main()
