import importlib.util
import json
from pathlib import Path
import sys

folder = Path(__file__).resolve().parents[2] / 'ai/data'
sys.path.insert(0, str(folder))
spec = importlib.util.spec_from_file_location('reanalyze_cached_spans', folder / 'reanalyze_cached_spans.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_partial_video_is_reported_but_not_used_in_complete_metrics(tmp_path, monkeypatch):
    tasks = {'schema_version': 1, 'videos': [
        {'id': 'a', 'split': 'train', 'fps': 10, 'frame_count': 100, 'annotation_status': 'needs_review', 'reps': [{'start_frame': 5, 'bottom_frame': 10, 'end_frame': 15}]},
    ]}
    (tmp_path / 'a_pose.json').write_text(json.dumps({'frames': []}), encoding='utf8')
    monkeypatch.setattr(module, 'analyze_detected_spans', lambda *args, **kwargs: {
        'status': 'partial', 'missing_frames': 1, 'total_frames': 100, 'analyzed_frames': 99,
        'reps': [{'bottom_frame': 10}], 'warning': 'partial count'})
    result = module.analyze_cached(tasks, tmp_path)
    assert result['videos'][0]['status'] == 'partial'
    assert result['complete_only']['train']['summary']['videos'] == 0
    assert result['complete_only']['train']['summary']['precision'] is None
