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
