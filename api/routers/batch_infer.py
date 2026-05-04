"""批量推理任务 + 通用任务查询。"""
from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.auth_core import require_roles
from api.batch_worker import spawn_infer_batch_thread
from api.deps import get_db
from db.models import AsyncJob
from db.repository import JobRepository

router_infer_batch = APIRouter(prefix="/api/v1/infer", tags=["infer"])
router_jobs = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class InferBatchBody(BaseModel):
    image_ids: list[int] = Field(..., min_length=1, max_length=200)
    topk: int = Field(default=3, ge=1, le=10)


class InferBatchSubmitResponse(BaseModel):
    job_id: str
    status: str
    message: str = "任务已排队；可轮询 GET /api/v1/jobs/{job_id} 取结果"


@router_infer_batch.post("/batch", response_model=InferBatchSubmitResponse)
def infer_batch(
    body: InferBatchBody,
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
    db: Annotated[Session, Depends(get_db)],
):
    """对多张库内图片顺序推理（后台线程执行，避免长阻塞）。"""
    repo = JobRepository(db)
    job = repo.add_infer_batch_pending(body.image_ids, body.topk)
    spawn_infer_batch_thread(job.id)
    return InferBatchSubmitResponse(job_id=job.id, status="pending")


@router_jobs.get("/{job_id}", response_model=dict)
def get_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
):
    row = db.get(AsyncJob, job_id)
    if not row:
        raise HTTPException(status_code=404, detail="任务不存在")
    out: dict[str, Any] = {
        "id": row.id,
        "job_type": row.job_type,
        "status": row.status,
        "error_message": row.error_message,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
    }
    if row.payload_json:
        out["payload"] = json.loads(row.payload_json)
    if row.result_json:
        out["result"] = json.loads(row.result_json)
    return out
