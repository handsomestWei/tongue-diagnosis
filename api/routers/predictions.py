"""预测结果查询与纠错（P4-1 基线）。"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth_core import require_roles
from api.config import Settings, get_settings
from api.deps import get_db
from db.models import Correction, Prediction
from db.repository import ImageRepository

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


class PredictionListOut(BaseModel):
    id: int
    image_id: int
    model_id: int
    pred_class: Optional[str]
    confidence: Optional[float]
    demo: bool = False
    created_at: Optional[datetime]


class CorrectionBody(BaseModel):
    correct_class: str = Field(..., min_length=1, max_length=128)
    remark: Optional[str] = None
    include_in_next_train: bool = False


@router.get("", response_model=list[PredictionListOut])
def list_predictions(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
    limit: int = 100,
):
    rows = db.scalars(select(Prediction).order_by(Prediction.id.desc()).limit(min(limit, 500))).all()
    out: list[PredictionListOut] = []
    for r in rows:
        pred_class, conf, demo = None, None, False
        try:
            j = json.loads(r.result_json or "{}")
            demo = bool(j.get("demo", False))
            t = j.get("topk") or []
            if t:
                pred_class = str(t[0].get("class", ""))
                conf = t[0].get("score")
        except (json.JSONDecodeError, TypeError, IndexError):
            pass
        out.append(
            PredictionListOut(
                id=r.id,
                image_id=r.image_id,
                model_id=r.model_id,
                pred_class=pred_class,
                confidence=conf,
                demo=demo,
                created_at=r.created_at,
            )
        )
    return out


@router.post("/{prediction_id}/correct", response_model=dict)
def submit_correction(
    prediction_id: int,
    body: CorrectionBody,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator"))],
):
    pred = db.get(Prediction, prediction_id)
    if not pred:
        raise HTTPException(status_code=404, detail="预测不存在")
    c = Correction(
        prediction_id=prediction_id,
        correct_class=body.correct_class,
        remark=body.remark,
        include_in_next_train=body.include_in_next_train,
    )
    db.add(c)
    repo = ImageRepository(db, settings)
    repo.replace_manual_label(pred.image_id, body.correct_class)
    db.commit()
    return {"ok": True, "prediction_id": prediction_id, "image_id": pred.image_id}
