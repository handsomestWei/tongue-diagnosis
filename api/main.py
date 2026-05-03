from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routers import auth as auth_router
from api.routers import batch_infer as batch_infer_router
from api.routers import images as images_router
from api.routers import predictions as predictions_router
from api.routers import training as training_router
from api.routers import infer as infer_router
from db.seed import init_db_schema_and_seed
from db.session import configure_engine
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
    configure_engine(settings)
    init_db_schema_and_seed(settings)
    yield


app = FastAPI(
    title="Tongue Diagnosis API",
    version="0.4.0",
    description="舌象平台 API：训练导出、后台训练、推理持久化与纠错。",
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
