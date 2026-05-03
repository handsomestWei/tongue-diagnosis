"""训练任务与模型注册 API（P3）。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth_core import require_roles
from api.deps import get_db
from api.train_worker import spawn_train_job_thread
from db.models import ModelRegistry, TrainJob, TrainJobStatus

router_train = APIRouter(prefix="/api/v1/train", tags=["train"])
router_models = APIRouter(prefix="/api/v1/models", tags=["models"])


class TrainSubmitBody(BaseModel):
    data_version: str = "default"
    model: str = "yolov8n-cls.pt"
    epochs: int = Field(default=1, ge=1, le=500)
    imgsz: int = Field(default=224, ge=32)
    batch: int = Field(default=4, ge=1)
    val_ratio: float = Field(default=0.2, ge=0.05, le=0.5)
    seed: int = Field(default=42)
    margin: float = Field(default=0.12)
    letterbox: bool = True
    clahe: bool = True
    unsharp: bool = False
    register_name: Optional[str] = None
    set_as_default: bool = False


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
    payload = body.model_dump()
    job = TrainJob(
        status=TrainJobStatus.pending.value,
        params_json=json.dumps(payload, ensure_ascii=False),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    spawn_train_job_thread(job.id)
    return TrainJobOut(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        message="训练已在后台启动（导出 YOLO 数据 + Ultralytics classify；见 GET /api/v1/train/{id}）",
    )


class IncrementalTrainBody(BaseModel):
    parent_model_id: int
    data_version: str = "incremental"
    model: str = "yolov8n-cls.pt"
    epochs: int = Field(default=5, ge=1, le=200)
    imgsz: int = Field(default=224, ge=32)
    batch: int = Field(default=4, ge=1)
    selection: str = Field(
        default="corrections_merged",
        description="corrections_merged=全量 manual + 勾选纠错覆盖类别；corrections_only=仅勾选纠错样本；all_manual=等同全量导出",
    )
    register_name: Optional[str] = None


@router_train.post("/incremental", response_model=TrainJobOut)
def submit_incremental(
    body: IncrementalTrainBody,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator"))],
):
    parent = db.get(ModelRegistry, body.parent_model_id)
    if not parent:
        raise HTTPException(status_code=400, detail="parent_model_id 不存在")
    if not Path(parent.path).expanduser().is_file():
        raise HTTPException(status_code=400, detail="父模型路径不可读，无法增量微调")

    sel = (body.selection or "corrections_merged").strip().lower()
    legacy = {"corrections_with_flag": "corrections_merged"}
    sel = legacy.get(sel, sel)
    if sel == "all_manual":
        export_selection = "all_manual"
        merge_base = False
    elif sel in ("corrections_only", "corrections_flagged"):
        export_selection = "corrections_flagged"
        merge_base = False
    elif sel in ("corrections_merged", "merged"):
        export_selection = "corrections_flagged"
        merge_base = True
    else:
        raise HTTPException(
            status_code=400,
            detail="selection 须为 all_manual | corrections_only | corrections_merged",
        )

    payload = {
        "job_subtype": "incremental",
        "parent_model_id": body.parent_model_id,
        "parent_weights": parent.path,
        "data_version": body.data_version,
        "model": body.model,
        "epochs": body.epochs,
        "imgsz": body.imgsz,
        "batch": body.batch,
        "selection": body.selection,
        "export_selection": export_selection,
        "merge_base_manual": merge_base,
        "register_name": body.register_name or f"incremental-{body.parent_model_id}",
    }
    job = TrainJob(
        status=TrainJobStatus.pending.value,
        params_json=json.dumps(payload, ensure_ascii=False),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    spawn_train_job_thread(job.id)
    return TrainJobOut(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        message="增量任务已启动（按 selection 导出子集；父权重作为微调起点）",
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
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
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
