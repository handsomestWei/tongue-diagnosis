"""推理占位（P2 前序）：校验 image_kind，返回固定演示 JSON。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from api.auth_core import require_roles

router = APIRouter(prefix="/api/v1/infer", tags=["infer"])


class InferDemoResponse(BaseModel):
    demo: bool = True
    message: str
    image_kind: str
    topk: list[dict]


@router.post("", response_model=InferDemoResponse)
async def infer_demo(
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
    image_kind: str = Form(...),
    file: UploadFile | None = File(None),
    topk: int = Form(default=3),
):
    allowed = {"full_face_selfie", "tongue_closeup"}
    if image_kind not in allowed:
        raise HTTPException(status_code=400, detail=f"无效 image_kind，允许 {sorted(allowed)}")
    fname = file.filename if file else None
    if file:
        await file.read()
    k = max(1, min(topk, 10))
    rankings = [
        {"class": "淡红舌", "score": 0.42},
        {"class": "红舌", "score": 0.31},
        {"class": "淡白舌", "score": 0.12},
        {"class": "紫舌", "score": 0.08},
    ]
    return InferDemoResponse(
        message=f"演示推理（未加载模型）；文件={fname or 'none'}",
        image_kind=image_kind,
        topk=rankings[:k],
    )
