"""批量推理任务 + 通用任务查询。"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.auth_core import require_roles
from api.config import Settings, get_settings
from api.deps import get_db
from api.infer_runner import run_infer_for_db_image
from db.models import AsyncJob, AsyncJobStatus
from db.repository import ImageRepository

router_infer_batch = APIRouter(prefix="/api/v1/infer", tags=["infer"])
router_jobs = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])
log = logging.getLogger(__name__)


class InferBatchBody(BaseModel):
    image_ids: list[int] = Field(..., min_length=1, max_length=200)
    topk: int = Field(default=3, ge=1, le=10)


class InferBatchSubmitResponse(BaseModel):
    job_id: str
    status: str
    message: str = "已执行（同步）；可 GET /api/v1/jobs/{job_id} 取结果"


@router_infer_batch.post("/batch", response_model=InferBatchSubmitResponse)
def infer_batch(
    body: InferBatchBody,
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
):
    """对多张库内图片顺序推理（当前进程内同步执行，完成后写 `async_jobs`）。"""
    repo = ImageRepository(db, settings)
    job = AsyncJob(
        job_type="infer_batch",
        status=AsyncJobStatus.running.value,
        payload_json=json.dumps({"image_ids": body.image_ids, "topk": body.topk}),
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    jid = job.id

    items: list[dict[str, Any]] = []
    err_list: list[dict[str, Any]] = []
    try:
        for iid in body.image_ids:
            row = repo.get(iid)
            if row is None:
                err_list.append({"image_id": iid, "error": "图片不存在"})
                continue
            try:
                out = run_infer_for_db_image(settings, repo, row, body.topk)
                items.append({"image_id": iid, "image_kind": row.image_kind, **out})
            except FileNotFoundError as e:
                err_list.append({"image_id": iid, "error": str(e)})
            except RuntimeError as e:
                log.warning("batch infer %s: %s", iid, e)
                err_list.append({"image_id": iid, "error": str(e)})
            except Exception as e:
                log.exception("batch infer %s", iid)
                err_list.append({"image_id": iid, "error": str(e)})

        job = db.get(AsyncJob, jid)
        if job:
            job.status = AsyncJobStatus.success.value
            job.result_json = json.dumps({"items": items, "errors": err_list}, ensure_ascii=False)
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
        return InferBatchSubmitResponse(job_id=jid, status="success")
    except Exception as e:
        log.exception("infer_batch job %s", jid)
        job = db.get(AsyncJob, jid)
        if job:
            job.status = AsyncJobStatus.failed.value
            job.error_message = str(e)
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
        raise HTTPException(status_code=500, detail=str(e)) from e


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
