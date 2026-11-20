import importlib.util
from pathlib import Path
import sys

folder = Path(__file__).resolve().parents[2] / 'ai/data'
sys.path.insert(0, str(folder))
spec = importlib.util.spec_from_file_location('exploratory_rep_baseline', folder / 'exploratory_rep_baseline.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_failed_video_does_not_become_a_zero_rep_prediction():
    tasks = {'videos': [
        {'id': 'a', 'split': 'train', 'fps': 10, 'reps': [{'bottom_frame': 10}]},
        {'id': 'b', 'split': 'validation', 'fps': 10, 'reps': [{'bottom_frame': 20}]},
    ]}
    records = [{'id': 'a', 'status': 'ok', 'bottom_frames': [10]},
               {'id': 'b', 'status': 'failed', 'error': 'missing pose'}]
    result = module.summarize(tasks, records)
    assert result['attempted'] == 2 and result['successful'] == 1
    assert result['failures'][0]['id'] == 'b'
    assert result['by_split']['validation']['summary']['videos'] == 0
    assert result['by_split']['train']['summary']['true_positives'] == 1
    assert 'not ground truth' in result['interpretation']
