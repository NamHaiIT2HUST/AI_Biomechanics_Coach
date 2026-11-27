import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[2] / 'ai' / 'data' / 'audit_multiview.py'
spec = importlib.util.spec_from_file_location('audit_multiview', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(subject='s1', split='train', view='side', label='good', path='one.mp4'):
    return {'dataset': 'multiview', 'subject': subject, 'split': split, 'view': view,
            'video_label': label, 'label_scope': 'video', 'path': path, 'fps': 15, 'frames': 100}


def test_audit_reports_group_counts_without_decoding(tmp_path):
    (tmp_path / 'one.mp4').write_bytes(b'not a video')
    result = module.audit([row()], tmp_path)
    assert result['valid']
    assert result['by_split_view']['train/side'] == {'videos': 1, 'subjects': 1, 'labels': {'good': 1}}
    assert 'decode' in result['limitations'][0]


def test_audit_detects_subject_leakage_and_duplicate_paths(tmp_path):
    (tmp_path / 'one.mp4').write_bytes(b'')
    data = [row(), row(split='test', view='front')]
    result = module.audit(data, tmp_path)
    assert not result['valid']
    assert any('multiple splits' in error for error in result['errors'])
    assert any('duplicate path' in error for error in result['errors'])


def test_audit_rejects_unsafe_paths_bad_metadata_and_empty_manifest(tmp_path):
    result = module.audit([row(path='../outside.mp4'), row(subject='', path='x')], tmp_path)
    assert not result['valid']
    assert any('unsafe' in error for error in result['errors'])
    assert any('metadata' in error for error in result['errors'])
    assert not module.audit([], tmp_path)['valid']


def test_audit_rejects_duplicate_subject_view_label(tmp_path):
    (tmp_path / 'one.mp4').touch(); (tmp_path / 'two.mp4').touch()
    result = module.audit([row(), row(path='two.mp4')], tmp_path)
    assert any('duplicate subject/view/label' in error for error in result['errors'])
