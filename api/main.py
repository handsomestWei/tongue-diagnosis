from fastapi import FastAPI

app = FastAPI(
    title="Tongue Diagnosis API",
    version="0.1.0",
    description="服务化 API 骨架（P0）；后续接数据库与推理服务。",
)


@app.get("/health")
def health():
    return {"status": "ok"}
