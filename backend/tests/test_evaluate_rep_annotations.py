import importlib.util
from pathlib import Path
import sys
import pytest

folder = Path(__file__).resolve().parents[2] / 'ai/data'
sys.path.insert(0, str(folder))
spec = importlib.util.spec_from_file_location('evaluate_rep_annotations', folder / 'evaluate_rep_annotations.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def references():
    return {'schema_version': 1, 'videos': [
        {'id': 'a', 'split': 'train', 'fps': 10, 'frame_count': 100, 'annotation_status': 'reviewed', 'annotator': 'person', 'reps': [{'start_frame': 5, 'bottom_frame': 10, 'end_frame': 15}]},
        {'id': 'b', 'split': 'validation', 'fps': 10, 'frame_count': 100, 'annotation_status': 'reviewed', 'annotator': 'person', 'reps': [{'start_frame': 20, 'bottom_frame': 30, 'end_frame': 40}]},
    ]}


def test_evaluation_keeps_development_splits_separate():
    predictions = {'videos': [{'id': 'a', 'bottom_frames': [11]}, {'id': 'b', 'bottom_frames': []}]}
    result = module.evaluate_annotations(references(), predictions)
    assert result['train']['summary']['true_positives'] == 1
    assert result['validation']['summary']['false_negatives'] == 1


def test_incomplete_reference_and_missing_predictions_rejected():
    data = references()
    data['videos'][0]['annotation_status'] = 'unreviewed'
    with pytest.raises(ValueError, match='not reviewed'):
        module.evaluate_annotations(data, {'videos': []})
    with pytest.raises(ValueError, match='match exactly'):
        module.evaluate_annotations(references(), {'videos': [{'id': 'a', 'bottom_frames': []}]})


def test_out_of_range_prediction_is_rejected():
    with pytest.raises(ValueError, match='out of bounds'):
        module.evaluate_annotations(references(), {'videos': [{'id': 'a', 'bottom_frames': [100]}, {'id': 'b', 'bottom_frames': []}]})


def test_held_out_test_requires_explicit_opt_in_and_is_separate():
    data = references()
    data['videos'][1]['split'] = 'test'
    predictions = {'videos': [{'id': 'a', 'bottom_frames': [10]}, {'id': 'b', 'bottom_frames': [30], 'coverage_status': 'complete'}]}
    with pytest.raises(ValueError):
        module.evaluate_annotations(data, predictions)
    result = module.evaluate_annotations(data, predictions, include_test=True)
    assert result['test']['summary']['true_positives'] == 1
    assert result['validation']['summary']['videos'] == 0


def test_partial_test_video_is_excluded_and_recorded():
    data = references(); data['videos'][1]['split'] = 'test'
    predictions = {'videos': [{'id': 'a', 'bottom_frames': [10]}, {'id': 'b', 'bottom_frames': [], 'coverage_status': 'partial'}]}
    result = module.evaluate_annotations(data, predictions, include_test=True)
    assert result['test']['summary']['videos'] == 0
    assert result['test']['attempted_videos'] == 1
    assert result['test']['excluded'][0]['coverage_status'] == 'partial'


def test_test_predictions_require_coverage_status():
    data = references(); data['videos'][1]['split'] = 'test'
    predictions = {'videos': [{'id': 'a', 'bottom_frames': [10]}, {'id': 'b', 'bottom_frames': [30]}]}
    with pytest.raises(ValueError, match='coverage_status'):
        module.evaluate_annotations(data, predictions, include_test=True)


def test_same_subject_cannot_appear_across_splits():
    data = references()
    for video in data['videos']:
        video.update(dataset='multiview', subject='same_person')
    predictions = {'videos': [{'id': 'a', 'bottom_frames': [10]}, {'id': 'b', 'bottom_frames': [30]}]}
    with pytest.raises(ValueError, match='multiple splits'):
        module.evaluate_annotations(data, predictions)
