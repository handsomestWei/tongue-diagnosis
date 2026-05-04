from contextlib import asynccontextmanager
import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from api.config import get_settings
from api.logging_config import configure_structured_logging
from api.rate_limit import check_rate_limit
from api.routers import auth as auth_router
from api.routers import batch_infer as batch_infer_router
from api.routers import images as images_router
from api.routers import predictions as predictions_router
from api.routers import training as training_router
from api.routers import infer as infer_router
from db.seed import init_db_schema_and_seed
from db.session import configure_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_structured_logging(logging.INFO)
    os.environ["INFER_CONCURRENCY"] = str(settings.infer_concurrency)
    os.environ["INFER_SAM_CONCURRENCY"] = str(settings.infer_sam_concurrency)

    Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
    configure_engine(settings)
    init_db_schema_and_seed(settings)
    yield


app = FastAPI(
    title="Tongue Diagnosis API",
    version="0.5.0",
    description="舌象平台 API：批推理后台化、增量导出筛选、限流与结构化访问日志。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    blocked = check_rate_limit(request)
    if blocked is not None:
        return blocked
    return await call_next(request)


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    settings = get_settings()
    if not settings.access_log_enabled:
        return await call_next(request)
    rid = getattr(request.state, "request_id", None)
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
        dur = int((time.perf_counter() - t0) * 1000)
        logging.getLogger("api.access").info(
            "request",
            extra={
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": dur,
                "client": request.client.host if request.client else None,
            },
        )
        return response
    except Exception:
        dur = int((time.perf_counter() - t0) * 1000)
        logging.getLogger("api.access").exception(
            "request_failed",
            extra={
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": dur,
                "client": request.client.host if request.client else None,
            },
        )
        raise


app.include_router(auth_router.router)
app.include_router(images_router.router)
app.include_router(infer_router.router)
app.include_router(training_router.router_train)
app.include_router(training_router.router_models)
app.include_router(predictions_router.router)
app.include_router(batch_infer_router.router_infer_batch)
app.include_router(batch_infer_router.router_jobs)


@app.get("/health")
def health():
    return {"status": "ok"}
