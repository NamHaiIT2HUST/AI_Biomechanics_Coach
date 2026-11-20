import importlib.util
from pathlib import Path
import zipfile
import pytest

MODULE = Path(__file__).resolve().parents[2] / 'ai/data/prepare_squat_datasets.py'
spec = importlib.util.spec_from_file_location('prepare_squat_datasets', MODULE)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def test_splits_are_deterministic_and_keep_subjects_together():
    subjects = [f'subject_{i:03}' for i in range(25)]
    result = prepare.group_splits(subjects + subjects)
    assert result == prepare.group_splits(list(reversed(subjects)))
    assert set(result) == set(subjects)
    assert set(result.values()) == {'train', 'validation', 'test'}


def test_archive_extraction_reuses_identical_files_and_protects_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(prepare, 'OUTPUT', tmp_path / 'out')
    archive = tmp_path / 'data.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('data.txt', 'source data')
    with zipfile.ZipFile(archive) as z:
        target = prepare.extract_entry(z, 'data.txt', Path('subset/data.txt'))
        assert target.read_text() == 'source data'
        assert prepare.extract_entry(z, 'data.txt', Path('subset/data.txt')) == target
        with pytest.raises(ValueError, match='Unsafe'):
            prepare.extract_entry(z, 'data.txt', Path('../outside.txt'))
        target.write_text('user data')
        with pytest.raises(FileExistsError):
            prepare.extract_entry(z, 'data.txt', Path('subset/data.txt'))
        assert target.read_text() == 'user data'


def test_filename_patterns_preserve_source_labels():
    match = prepare.MULTI_PATTERN.fullmatch('Dataset Exercise-wise/squat/bad/side/subject_003_squat_bad_side.mp4')
    assert match.groups() == ('bad', 'side', 'subject_003')
    assert not prepare.MULTI_PATTERN.fullmatch('Dataset Exercise-wise/squat/bad/side/subject_003_squat_good_side.mp4')
