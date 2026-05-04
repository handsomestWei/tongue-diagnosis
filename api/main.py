from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth as auth_router

app = FastAPI(
    title="Tongue Diagnosis API",
    version="0.1.0",
    description="服务化 API；含 JWT 登录（演示用户）与 /health。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
