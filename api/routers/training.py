"""训练/模型占位 API（P3 进度），需鉴权。"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth_core import require_roles
from api.deps import get_db
from db.models import ModelRegistry, TrainJob, TrainJobStatus

router_train = APIRouter(prefix="/api/v1/train", tags=["train"])
router_models = APIRouter(prefix="/api/v1/models", tags=["models"])


class TrainSubmitBody(BaseModel):
    data_version: str = "default"
    model: str = "yolov8n-cls.pt"
    epochs: int = Field(default=1, ge=1, le=500)
    imgsz: int = Field(default=224, ge=32)
    batch: int = Field(default=4, ge=1)


class TrainJobOut(BaseModel):
    id: str
    status: str
    created_at: datetime
    message: str


class TrainJobListOut(BaseModel):
    id: str
    status: str
    created_at: datetime
    message: str = ""


@router_train.get("", response_model=list[TrainJobListOut])
def list_train_jobs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
    limit: int = 50,
):
    rows = db.scalars(select(TrainJob).order_by(TrainJob.created_at.desc()).limit(limit)).all()
    return [
        TrainJobListOut(
            id=r.id,
            status=r.status,
            created_at=r.created_at,
            message=(r.error_message or "")[:200],
        )
        for r in rows
    ]


@router_train.post("", response_model=TrainJobOut)
def submit_train(
    body: TrainSubmitBody,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator"))],
):
    job = TrainJob(
        status=TrainJobStatus.pending.value,
        params_json=json.dumps(body.model_dump()),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return TrainJobOut(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        message="已入队（占位：尚未执行 YOLO 训练）",
    )


@router_train.get("/{train_id}", response_model=dict)
def get_train(
    train_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
):
    row = db.get(TrainJob, train_id)
    if not row:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    return {
        "id": row.id,
        "status": row.status,
        "params": json.loads(row.params_json or "{}"),
        "log_path": row.log_path,
        "metrics": json.loads(row.metrics_json or "null"),
        "error_message": row.error_message,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


class ModelOut(BaseModel):
    id: int
    name: str
    path: str
    is_default: bool
    status: str


@router_models.get("", response_model=list[ModelOut])
def list_models(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
):
    rows = db.scalars(select(ModelRegistry).order_by(ModelRegistry.id.desc())).all()
    return [
        ModelOut(
            id=r.id,
            name=r.name,
            path=r.path,
            is_default=r.is_default,
            status=r.status,
        )
        for r in rows
    ]


class ModelRegisterBody(BaseModel):
    name: str
    path: str
    set_default: bool = False


@router_models.post("", response_model=ModelOut)
def register_model(
    body: ModelRegisterBody,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin"))],
):
    if body.set_default:
        for m in db.scalars(select(ModelRegistry).where(ModelRegistry.is_default.is_(True))).all():
            m.is_default = False
            db.add(m)
    row = ModelRegistry(name=body.name, path=body.path, is_default=body.set_default)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ModelOut(
        id=row.id,
        name=row.name,
        path=row.path,
        is_default=row.is_default,
        status=row.status,
    )
