from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routers import auth as auth_router
from api.routers import images as images_router
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
    version="0.3.0",
    description="舌象平台 API：鉴权、图片/标注、训练占位、推理（YOLO + 可选 TongueSAM）。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(images_router.router)
app.include_router(training_router.router_train)
app.include_router(training_router.router_models)
app.include_router(infer_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
