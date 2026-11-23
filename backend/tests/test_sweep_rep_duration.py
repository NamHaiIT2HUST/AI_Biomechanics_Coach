import importlib.util
import json
from pathlib import Path
import sys

import pytest

folder = Path(__file__).resolve().parents[2] / 'ai' / 'data'
sys.path.insert(0, str(folder))
spec = importlib.util.spec_from_file_location('sweep_rep_duration', folder / 'sweep_rep_duration.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def task(vid, split):
    return {'id': vid, 'split': split, 'fps': 10, 'frame_count': 30,
            'annotation_status': 'needs_review', 'reps': [{'start_frame': 2, 'bottom_frame': 10, 'end_frame': 20}]}


def test_sweep_uses_train_only_and_excludes_partial_from_metrics(tmp_path, monkeypatch):
    reference = {'schema_version': 1, 'videos': [task('complete', 'train'), task('partial', 'train'), task('heldout', 'validation')]}
    for name in ('complete', 'partial'):
        (tmp_path / f'{name}_pose.json').write_text(json.dumps({'fps': 10, 'frames': [None] * 30, 'name': name}), encoding='utf8')
    calls = []
    def analyze(pose, *, min_duration_s):
        calls.append((pose['name'], min_duration_s))
        return {'status': pose['name'], 'missing_frames': int(pose['name'] == 'partial'),
                'reps': [{'bottom_frame': 10}]}
    monkeypatch.setattr(module, 'analyze_detected_spans', analyze)
    result = module.sweep(reference, tmp_path, [0.8, 1.0])
    assert set(calls) == {('complete', .8), ('complete', 1.0), ('partial', .8), ('partial', 1.0)}
    for group in result['results'].values():
        assert group['complete_only']['summary']['videos'] == 1
        assert group['complete_only']['summary']['true_positives'] == 1
        assert {video['id'] for video in group['videos']} == {'complete', 'partial'}


@pytest.mark.parametrize('durations', [[], [0], [float('nan')], [0.8, 0.8]])
def test_invalid_duration_grid_is_rejected(tmp_path, durations):
    with pytest.raises(ValueError, match='Durations'):
        module.sweep({'schema_version': 1, 'videos': [task('one', 'train')]}, tmp_path, durations)


def test_mismatched_cached_pose_is_reported_as_failure(tmp_path):
    (tmp_path / 'one_pose.json').write_text(json.dumps({'fps': 12, 'frames': [None] * 30}), encoding='utf8')
    result = module.sweep({'schema_version': 1, 'videos': [task('one', 'train')]}, tmp_path, [1.0])
    assert result['results']['1.0']['videos'][0]['status'] == 'failed'
    assert result['results']['1.0']['complete_only']['summary']['videos'] == 0
