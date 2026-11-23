import threading
import time
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.analysis_store import AnalysisStore


@pytest.fixture
def mp4_bytes(tmp_path):
    path = tmp_path / 'input.mp4'
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), 15.0, (64, 64))
    if not writer.isOpened():
        pytest.skip('OpenCV MP4 encoder unavailable')
    for _ in range(5):
        writer.write(np.full((64, 64, 3), 127, dtype=np.uint8))
    writer.release()
    return path.read_bytes()


def wait_for(client, analysis_id, states, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f'/api/v1/analyses/{analysis_id}')
        if response.json()['status'] in states:
            return response.json()
        time.sleep(0.02)
    raise AssertionError('Analysis did not reach expected status')


def test_upload_status_result_video_and_restart(tmp_path, mp4_bytes):
    entered = threading.Event(); release = threading.Event()
    def runner(path, *, camera_view):
        assert Path(path).is_file() and camera_view == 'side_90deg'
        entered.set()
        assert release.wait(5)
        return {'outcome': 'reps_detected', 'detected_rep_count': 1}
    storage = tmp_path / 'store'
    app = create_app(storage_dir=storage, runner=runner)
    with TestClient(app) as client:
        assert client.get('/health').json()['status'] == 'healthy'
        assert client.get('/api/v1/exercises').json()['exercises'][0]['id'] == 'squat'
        response = client.post('/api/v1/analyses', files={'file': ('input.mp4', mp4_bytes, 'video/mp4')}, data={'camera_view': 'side_90deg'})
        assert response.status_code == 202, response.text
        analysis_id = response.json()['id']
        try:
            assert entered.wait(5)
            assert client.get(f'/api/v1/analyses/{analysis_id}').json()['status'] == 'processing'
            stream = client.get(f'/api/v1/analyses/{analysis_id}/video')
            assert stream.status_code == 200 and stream.content == mp4_bytes
            assert stream.headers['content-type'] == 'video/mp4'
        finally:
            release.set()
        done = wait_for(client, analysis_id, {'completed', 'failed'})
        assert done['status'] == 'completed' and done['result']['detected_rep_count'] == 1
    with TestClient(create_app(storage_dir=storage, runner=runner)) as client:
        assert client.get(f'/api/v1/analyses/{analysis_id}').json()['result']['outcome'] == 'reps_detected'


def test_invalid_uploads_rejected_and_partial_files_removed(tmp_path, mp4_bytes):
    storage = tmp_path / 'store'
    app = create_app(storage_dir=storage, max_upload_bytes=len(mp4_bytes) + 1)
    with TestClient(app) as client:
        url = '/api/v1/analyses'
        assert client.post(url, files={'file': ('file.txt', b'a', 'text/plain')}, data={'camera_view': 'side_90deg'}).status_code == 415
        assert client.post(url, files={'file': ('file.mp4', b'not video', 'video/mp4')}, data={'camera_view': 'side_90deg'}).status_code == 422
        assert client.post(url, files={'file': ('file.mp4', b'x' * (len(mp4_bytes) + 2), 'video/mp4')}, data={'camera_view': 'side_90deg'}).status_code == 413
        assert client.post(url, files={'file': ('file.mp4', mp4_bytes, 'video/mp4')}, data={'camera_view': 'invalid'}).status_code == 422
        assert client.get('/api/v1/analyses/not-a-uuid').status_code == 422
        assert client.get(f'/api/v1/analyses/{uuid4()}').status_code == 404
    assert list((storage / 'videos').iterdir()) == []


def test_failure_is_reported_without_internal_details(tmp_path, mp4_bytes):
    def runner(*args, **kwargs):
        raise RuntimeError('internal sensitive details')
    with TestClient(create_app(storage_dir=tmp_path / 'store', runner=runner)) as client:
        response = client.post('/api/v1/analyses', files={'file': ('file.mp4', mp4_bytes, 'video/mp4')}, data={'camera_view': 'unknown'})
        assert response.status_code == 202
        result = wait_for(client, response.json()['id'], {'failed'})
        assert result['error'] == 'analysis_failed'
        assert result['result'] is None
        assert 'internal sensitive details' not in str(result)


def test_restart_marks_unfinished_jobs_interrupted(tmp_path):
    storage = tmp_path / 'store'; store = AnalysisStore(storage)
    queued, processing = str(uuid4()), str(uuid4())
    store.create(queued, queued + '.mp4', 'side_90deg')
    store.create(processing, processing + '.mp4', 'side_90deg')
    store.start(processing)
    with TestClient(create_app(storage_dir=storage, runner=lambda *_args, **_kwargs: {})) as client:
        for key in (queued, processing):
            job = client.get(f'/api/v1/analyses/{key}').json()
            assert job['status'] == 'failed' and job['error'] == 'interrupted'


def test_upload_collision_never_deletes_existing_temporary_file(tmp_path, monkeypatch):
    import app.api.analyses as api
    fixed = uuid4()
    monkeypatch.setattr(api, 'uuid4', lambda: fixed)
    storage = tmp_path / 'store'
    with TestClient(create_app(storage_dir=storage)) as client:
        existing = storage / 'videos' / (str(fixed) + '.upload')
        existing.write_bytes(b'keep me')
        with pytest.raises(FileExistsError):
            client.post('/api/v1/analyses', files={'file': ('video.mp4', b'data', 'video/mp4')}, data={'camera_view': 'side_90deg'})
        assert existing.read_bytes() == b'keep me'


def test_delete_rejects_processing_then_removes_completed_job_and_video(tmp_path, mp4_bytes):
    entered = threading.Event(); release = threading.Event()
    def runner(path, *, camera_view):
        entered.set()
        assert release.wait(5)
        return {'outcome': 'no_reps_detected'}
    storage = tmp_path / 'store'
    with TestClient(create_app(storage_dir=storage, runner=runner)) as client:
        upload = client.post('/api/v1/analyses', files={'file': ('input.mp4', mp4_bytes, 'video/mp4')}, data={'camera_view': 'unknown'})
        key = upload.json()['id']
        try:
            assert entered.wait(5)
            assert client.delete(f'/api/v1/analyses/{key}').status_code == 409
            assert (storage / 'videos' / (key + '.mp4')).exists()
        finally:
            release.set()
        assert wait_for(client, key, {'completed'})['status'] == 'completed'
        assert client.delete(f'/api/v1/analyses/{key}').status_code == 204
        assert client.get(f'/api/v1/analyses/{key}').status_code == 404
        assert client.get(f'/api/v1/analyses/{key}/video').status_code == 404
        assert client.delete(f'/api/v1/analyses/{key}').status_code == 404
        assert not (storage / 'videos' / (key + '.mp4')).exists()


def test_delete_failure_preserves_record_and_video(tmp_path, monkeypatch):
    storage = tmp_path / 'store'; store = AnalysisStore(storage)
    key = str(uuid4()); store.create(key, key + '.mp4', 'unknown'); store.fail(key, 'interrupted')
    video = storage / 'videos' / (key + '.mp4'); video.write_bytes(b'keep')
    original_unlink = Path.unlink
    def fail_target(path, *args, **kwargs):
        if path == video:
            raise PermissionError('locked')
        return original_unlink(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'unlink', fail_target)
    with TestClient(create_app(storage_dir=storage)) as client:
        assert client.delete(f'/api/v1/analyses/{key}').status_code == 503
        assert client.get(f'/api/v1/analyses/{key}').status_code == 200
        assert video.read_bytes() == b'keep'
