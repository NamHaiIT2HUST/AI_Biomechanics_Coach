import importlib.util
import json
from pathlib import Path
import sys
import pytest

folder = Path(__file__).resolve().parents[2] / 'ai/data'
sys.path.insert(0, str(folder))
spec = importlib.util.spec_from_file_location('label_reps', folder / 'label_reps.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_save_preserves_existing_file_when_temporary_file_exists(tmp_path):
    path = tmp_path / 'tasks.json'
    path.write_text('original', encoding='utf8')
    (tmp_path / 'tasks.json.tmp').write_text('unsaved work', encoding='utf8')
    data = {'schema_version': 1, 'videos': []}
    with pytest.raises(FileExistsError):
        module.save_tasks(path, data)
    assert path.read_text(encoding='utf8') == 'original'
    assert (tmp_path / 'tasks.json.tmp').read_text(encoding='utf8') == 'unsaved work'


def test_save_writes_validated_annotations(tmp_path):
    path = tmp_path / 'tasks.json'
    data = {'schema_version': 1, 'videos': []}
    module.save_tasks(path, data)
    assert json.loads(path.read_text(encoding='utf8')) == data
