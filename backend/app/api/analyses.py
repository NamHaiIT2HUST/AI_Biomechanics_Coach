"""Squat video analysis endpoints."""
from concurrent.futures import ThreadPoolExecutor
import logging
import math
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

import cv2
from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.core.pipeline import load_squat_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/v1', tags=['analyses'])
CameraView = Literal['side_90deg', 'front_0deg', 'unknown']
JobStatus = Literal['queued', 'processing', 'completed', 'failed']


class AnalysisResponse(BaseModel):
    id: UUID
    status: JobStatus
    created_at: str
    updated_at: str
    result: dict[str, Any] | None = None
    error: str | None = None


def response(row):
    return AnalysisResponse(**row)


def check_video(path: Path):
    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise ValueError('Video could not be opened')
        fps = capture.get(cv2.CAP_PROP_FPS)
        width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if not all(math.isfinite(value) and value > 0 for value in (fps, width, height)):
            raise ValueError('Video metadata is invalid')
        ok, _ = capture.read()
        if not ok:
            raise ValueError('Video has no decodable frames')
    finally:
        capture.release()


def process_job(store, analysis_id: str, runner):
    if not store.start(analysis_id):
        return
    row = store.get(analysis_id)
    try:
        result = runner(store.video_dir / row['video_name'], camera_view=row['camera_view'])
        store.finish(analysis_id, result)
    except Exception:
        logger.exception('Analysis %s failed', analysis_id)
        store.fail(analysis_id, 'analysis_failed')


@router.get('/exercises')
def get_exercises():
    config = load_squat_config()
    return {'exercises': [{'id': config['id'], 'name': config['name'], 'camera': config['camera']}]}


@router.post('/analyses', response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    request: Request,
    file: UploadFile = File(...),
    exercise_id: Literal['squat'] = Form('squat'),
    camera_view: CameraView = Form(...),
):
    extension = Path(file.filename or '').suffix.lower()
    if extension not in ('.mp4', '.mov'):
        await file.close()
        raise HTTPException(status_code=415, detail='Only MP4 or MOV videos are supported.')
    store = request.app.state.analysis_store
    analysis_id = str(uuid4())
    video_name = analysis_id + extension
    target = store.video_dir / video_name
    temporary = store.video_dir / (analysis_id + '.upload')
    stored = False
    owns_temporary = False
    owns_target = False
    try:
        size = 0
        with temporary.open('xb') as out:
            owns_temporary = True
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > request.app.state.max_upload_bytes:
                    raise HTTPException(status_code=413, detail='Video exceeds the upload size limit.')
                out.write(chunk)
        if size == 0:
            raise HTTPException(status_code=422, detail='Video file is empty.')
        try:
            await run_in_threadpool(check_video, temporary)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        # Reserve our destination exclusively; never overwrite an existing video.
        with target.open('xb'):
            owns_target = True
        temporary.replace(target)
        owns_temporary = False
        store.create(analysis_id, video_name, camera_view)
        stored = True
        try:
            request.app.state.analysis_executor.submit(process_job, store, analysis_id, request.app.state.analysis_runner)
        except RuntimeError as exc:
            store.fail(analysis_id, 'worker_unavailable')
            raise HTTPException(status_code=503, detail='Analysis worker is unavailable.') from exc
        return response(store.get(analysis_id))
    finally:
        await file.close()
        if not stored:
            if owns_temporary:
                temporary.unlink(missing_ok=True)
            if owns_target:
                target.unlink(missing_ok=True)


@router.get('/analyses/{analysis_id}', response_model=AnalysisResponse)
def get_analysis(analysis_id: UUID, request: Request):
    row = request.app.state.analysis_store.get(str(analysis_id))
    if row is None:
        raise HTTPException(status_code=404, detail='Analysis not found.')
    return response(row)


@router.delete('/analyses/{analysis_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: UUID, request: Request):
    try:
        outcome = request.app.state.analysis_store.delete_terminal(str(analysis_id))
    except (OSError, ValueError):
        logger.exception('Could not delete analysis %s', analysis_id)
        raise HTTPException(status_code=503, detail='Could not remove analysis video; try again after closing it.')
    if outcome == 'not_found':
        raise HTTPException(status_code=404, detail='Analysis not found.')
    if outcome == 'busy':
        raise HTTPException(status_code=409, detail='Analysis is still processing.')
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/analyses/{analysis_id}/video', response_class=FileResponse)
def get_video(analysis_id: UUID, request: Request):
    store = request.app.state.analysis_store
    row = store.get(str(analysis_id))
    if row is None:
        raise HTTPException(status_code=404, detail='Analysis not found.')
    path = store.video_dir / row['video_name']
    if not path.is_file():
        raise HTTPException(status_code=404, detail='Video not found.')
    media_type = 'video/quicktime' if path.suffix == '.mov' else 'video/mp4'
    return FileResponse(path, media_type=media_type, filename='video' + path.suffix, content_disposition_type='inline')
