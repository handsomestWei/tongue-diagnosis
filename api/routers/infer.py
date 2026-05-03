"""推理：image_kind + 可选文件 或 image_id；可选真实 YOLO 权重。"""
from __future__ import annotations

import json
import logging
import time
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth_core import require_roles
from api.config import Settings, get_settings
from api.deps import get_db
from api.infer_runner import run_infer_for_db_image
from core.inference_service import _read_bgr_from_upload_bytes, run_infer
from db.models import ModelRegistry, Prediction
from db.repository import ImageRepository

router = APIRouter(prefix="/api/v1/infer", tags=["infer"])
log = logging.getLogger(__name__)

_ALLOWED = frozenset({"full_face_selfie", "tongue_closeup"})


def _truthy_form(v: Optional[str]) -> bool:
    if v is None:
        return False
    return str(v).strip().lower() in ("1", "true", "yes", "on")


class InferResponse(BaseModel):
    demo: bool
    message: str
    image_kind: str
    topk: list[dict]
    sam_called: bool = False
    sam_failed: bool = False
    prediction_id: Optional[int] = None


def _resolve_model_id(db: Session, model_id: Optional[int]) -> int:
    if model_id is not None:
        if db.get(ModelRegistry, model_id) is None:
            raise HTTPException(status_code=400, detail="model_id 不存在")
        return model_id
    m = db.scalar(select(ModelRegistry).where(ModelRegistry.is_default.is_(True)).limit(1))
    if m is None:
        m = db.scalar(select(ModelRegistry).order_by(ModelRegistry.id.desc()).limit(1))
    if m is None:
        raise HTTPException(status_code=400, detail="persist 需要指定 model_id 或先注册模型")
    return m.id


@router.post("", response_model=InferResponse)
async def infer(
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    image_kind: Optional[str] = Form(default=None),
    image_id: Optional[int] = Form(default=None),
    topk: int = Form(default=3),
    persist: Optional[str] = Form(default=None),
    model_id: Optional[int] = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    repo = ImageRepository(db, settings)
    pred_id: Optional[int] = None

    if image_id is not None:
        row = repo.get(image_id)
        if not row:
            raise HTTPException(status_code=404, detail="图片不存在")
        if image_kind is not None and image_kind != row.image_kind:
            raise HTTPException(
                status_code=400,
                detail=f"表单 image_kind 与库中记录不一致（库: {row.image_kind}, 表单: {image_kind}）",
            )
        tk = max(1, min(topk, 10))
        t0 = time.perf_counter()
        try:
            result = run_infer_for_db_image(settings, repo, row, tk)
        except FileNotFoundError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
        except RuntimeError as e:
            log.warning("infer runtime: %s", e)
            raise HTTPException(status_code=502, detail=str(e)) from e
        except Exception as e:
            log.exception("infer failed")
            raise HTTPException(status_code=500, detail=str(e)) from e
        latency_ms = int((time.perf_counter() - t0) * 1000)

        if _truthy_form(persist):
            mid = _resolve_model_id(db, model_id)
            payload = {**result, "topk": result.get("topk", []), "latency_ms": latency_ms}
            pr = Prediction(
                image_id=image_id,
                model_id=mid,
                result_json=json.dumps(payload, ensure_ascii=False),
                latency_ms=latency_ms,
            )
            db.add(pr)
            db.commit()
            db.refresh(pr)
            pred_id = pr.id

        return InferResponse(**result, prediction_id=pred_id)

    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail="请提供 image_id（库中图片）或上传 file，并配合 image_kind",
        )
    if image_kind is None or image_kind not in _ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=f"上传文件时须指定 image_kind，允许 {sorted(_ALLOWED)}",
        )
    if _truthy_form(persist):
        raise HTTPException(
            status_code=400,
            detail="persist 仅支持 image_id（请先将图片入库再推理）",
        )
    kind = image_kind
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")
    try:
        image_bgr = _read_bgr_from_upload_bytes(raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    tk = max(1, min(topk, 10))
    try:
        result = run_infer(
            settings,
            image_kind=kind,
            image_bgr=image_bgr,
            sam_source_path=None,
            topk=tk,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except RuntimeError as e:
        log.warning("infer runtime: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        log.exception("infer failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return InferResponse(**result)
