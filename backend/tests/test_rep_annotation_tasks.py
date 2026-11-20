import importlib.util
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[2] / 'ai/data/rep_annotation_tasks.py'
spec = importlib.util.spec_from_file_location('rep_annotation_tasks', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def video(**overrides):
    result = dict(id='a', split='train', fps=15.0, frame_count=100, annotation_status='reviewed', annotator='reviewer', reps=[])
    result.update(overrides)
    return {'schema_version': 1, 'videos': [result]}


def test_complete_requires_review_and_annotator():
    assert module.validate_tasks(video(), require_complete=True) == 1
    with pytest.raises(ValueError, match='not reviewed'):
        module.validate_tasks(video(annotation_status='unreviewed'), require_complete=True)
    with pytest.raises(ValueError, match='annotator'):
        module.validate_tasks(video(annotator=None), require_complete=True)


def test_empty_unreviewed_is_not_a_reviewed_zero_rep():
    assert module.validate_tasks(video(annotation_status='unreviewed', annotator=None)) == 1
    with pytest.raises(ValueError, match='not reviewed'):
        module.validate_tasks(video(annotation_status='unreviewed', annotator=None), require_complete=True)


def test_rejects_overlapping_or_out_of_bounds_marks():
    reps = [dict(start_frame=1, bottom_frame=5, end_frame=10), dict(start_frame=10, bottom_frame=15, end_frame=20)]
    with pytest.raises(ValueError, match='overlapping'):
        module.validate_tasks(video(reps=reps))
    with pytest.raises(ValueError, match='boundaries'):
        module.validate_tasks(video(reps=[dict(start_frame=1, bottom_frame=5, end_frame=100)]))


def test_test_split_is_not_used_for_development():
    with pytest.raises(ValueError, match='test'):
        module.validate_tasks(video(split='test'))


def test_build_tasks_selects_distinct_people_without_predictions(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'SUBJECTS', {'train': ('s1',), 'validation': ('s2',)})
    rows = []
    for subject, split in [('s1', 'train'), ('s2', 'validation')]:
        for label in ('good', 'bad'):
            name = f'{subject}_{label}.mp4'
            (tmp_path / name).write_bytes(b'video')
            rows.append(dict(dataset='multiview', split=split, subject=subject, view='side', video_label=label, path=name, fps=15.0, frames=100))
    result = module.build_tasks(rows, tmp_path)
    assert len(result['videos']) == 4
    assert all(v['annotation_status'] == 'unreviewed' and not v['reps'] for v in result['videos'])
    assert all('predictions' not in v for v in result['videos'])
    module.validate_tasks(result)
