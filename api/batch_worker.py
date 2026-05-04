"""后台执行 infer_batch（AsyncJob）：避免 HTTP 请求长时间阻塞。"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any

from api.config import get_settings
from api.infer_runner import run_infer_for_db_image
from db.models import AsyncJob, AsyncJobStatus
from db.repository import ImageRepository
from db.session import get_session_factory

log = logging.getLogger(__name__)


def run_infer_batch_job_background(job_id: str) -> None:
    settings = get_settings()
    SessionLocal = get_session_factory()
    with SessionLocal() as db:
        job = db.get(AsyncJob, job_id)
        if not job:
            log.error("AsyncJob missing: %s", job_id)
            return
        payload = json.loads(job.payload_json or "{}")
        image_ids = payload.get("image_ids") or []
        topk = int(payload.get("topk", 3))
        job.status = AsyncJobStatus.running.value
        job.started_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()

    items: list[dict[str, Any]] = []
    err_list: list[dict[str, Any]] = []

    try:
        for iid in image_ids:
            with SessionLocal() as db:
                repo = ImageRepository(db, settings)
                row = repo.get(int(iid))
                if row is None:
                    err_list.append({"image_id": iid, "error": "图片不存在"})
                    continue
                try:
                    out = run_infer_for_db_image(settings, repo, row, topk)
                    items.append({"image_id": int(iid), "image_kind": row.image_kind, **out})
                except FileNotFoundError as e:
                    err_list.append({"image_id": iid, "error": str(e)})
                except RuntimeError as e:
                    log.warning("batch infer %s: %s", iid, e)
                    err_list.append({"image_id": iid, "error": str(e)})
                except Exception as e:
                    log.exception("batch infer %s", iid)
                    err_list.append({"image_id": iid, "error": str(e)})
    except Exception as e:
        log.exception("infer_batch job %s", job_id)
        with SessionLocal() as db:
            job = db.get(AsyncJob, job_id)
            if job:
                job.status = AsyncJobStatus.failed.value
                job.error_message = str(e)
                job.finished_at = datetime.now(timezone.utc)
                db.add(job)
                db.commit()
        return

    with SessionLocal() as db:
        job = db.get(AsyncJob, job_id)
        if not job:
            return
        job.status = AsyncJobStatus.success.value
        job.result_json = json.dumps({"items": items, "errors": err_list}, ensure_ascii=False)
        job.finished_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()


def spawn_infer_batch_thread(job_id: str) -> None:
    t = threading.Thread(target=run_infer_batch_job_background, args=(job_id,), daemon=True)
    t.start()


__all__ = ["run_infer_batch_job_background", "spawn_infer_batch_thread"]
