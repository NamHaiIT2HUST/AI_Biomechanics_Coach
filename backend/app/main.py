from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyses import router
from app.config import settings
from app.core.pipeline import analyze_squat_video
from app.services.analysis_store import AnalysisStore


def create_app(*, storage_dir: Path | None = None, runner=None, max_upload_bytes: int | None = None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store = AnalysisStore(Path(storage_dir) if storage_dir is not None else settings.ANALYSES_DIR)
        store.mark_interrupted()
        app.state.analysis_store = store
        app.state.analysis_runner = runner if runner is not None else analyze_squat_video
        app.state.max_upload_bytes = max_upload_bytes if max_upload_bytes is not None else settings.MAX_UPLOAD_BYTES
        if app.state.max_upload_bytes <= 0:
            raise ValueError('Upload limit must be positive')
        app.state.analysis_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='analysis')
        try:
            yield
        finally:
            app.state.analysis_executor.shutdown(wait=True)

    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION,
                  description='Hệ thống phân tích video động tác gym.', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
                       allow_credentials=True, allow_methods=['GET', 'POST'], allow_headers=['*'])
    app.include_router(router)

    @app.get('/')
    def read_root():
        return {'app': settings.APP_NAME, 'version': settings.APP_VERSION, 'status': 'online', 'docs_url': '/docs'}

    @app.get('/health')
    def health_check():
        return {'status': 'healthy', 'app': settings.APP_NAME, 'version': settings.APP_VERSION}

    return app


app = create_app()
