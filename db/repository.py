"""数据访问封装（P1-3），便于单测 mock。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from api.config import Settings
from db.models import AsyncJob, AsyncJobStatus, Image, Label


class ImageRepository:
    def __init__(self, db: Session, settings: Settings):
        self._db = db
        self._settings = settings

    def get(self, image_id: int) -> Optional[Image]:
        return self._db.get(Image, image_id)

    def abs_storage_path(self, row: Image) -> Path:
        root = Path(self._settings.storage_root).resolve()
        return root / row.storage_path.replace("\\", "/")

    def set_derived_tongue_path(self, row: Image, rel: str) -> None:
        row.derived_tongue_path = rel.replace("\\", "/")
        self._db.add(row)
        self._db.commit()

    def replace_manual_label(self, image_id: int, class_name: str) -> None:
        row = self.get(image_id)
        if not row:
            raise ValueError("image not found")
        for lbl in list(row.labels):
            if lbl.source == "manual":
                self._db.delete(lbl)
        self._db.add(
            Label(
                image_id=image_id,
                class_name=class_name,
                source="manual",
                confidence=None,
            )
        )
        self._db.commit()


class JobRepository:
    """AsyncJob / 批任务等（薄封装，便于测试 mock）。"""

    def __init__(self, db: Session):
        self._db = db

    def get(self, job_id: str) -> AsyncJob | None:
        return self._db.get(AsyncJob, job_id)

    def add_infer_batch_pending(self, image_ids: list[int], topk: int) -> AsyncJob:
        job = AsyncJob(
            job_type="infer_batch",
            status=AsyncJobStatus.pending.value,
            payload_json=json.dumps({"image_ids": image_ids, "topk": topk}, ensure_ascii=False),
        )
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)
        return job
