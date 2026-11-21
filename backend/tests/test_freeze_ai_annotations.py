import importlib.util
from pathlib import Path
import sys
import pytest

folder = Path(__file__).resolve().parents[2] / 'ai/data'
sys.path.insert(0, str(folder))
spec = importlib.util.spec_from_file_location('freeze_ai_annotations', folder / 'freeze_ai_annotations.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_freeze_keeps_ai_draft_distinct_from_reviewed_ground_truth():
    data = {'schema_version': 1, 'videos': [{'id': 'x', 'split': 'train', 'fps': 15, 'frame_count': 100,
        'annotation_status': 'needs_review', 'reps': [{'start_frame': 1, 'bottom_frame': 10, 'end_frame': 20}],
        'review_provenance': {'annotator_type': 'AI'}}]}
    snapshot = module.freeze(data)
    assert snapshot['videos'][0]['annotation_status'] == 'needs_review'
    assert snapshot['snapshot']['independent_benchmark'] is False
    assert snapshot['snapshot']['usage'] == 'development_only'


def test_freeze_rejects_missing_ai_provenance():
    data = {'schema_version': 1, 'videos': [{'id': 'x', 'split': 'train', 'fps': 15, 'frame_count': 100,
        'annotation_status': 'needs_review', 'reps': [{'start_frame': 1, 'bottom_frame': 10, 'end_frame': 20}]}]}
    with pytest.raises(ValueError, match='AI provenance'):
        module.freeze(data)
