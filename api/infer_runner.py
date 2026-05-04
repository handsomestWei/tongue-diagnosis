"""单图推理编排（供 HTTP 层复用，避免 duplicated 逻辑）。"""
from __future__ import annotations

from pathlib import Path

from api.config import Settings
from core.inference_service import _read_bgr_from_upload_bytes, run_infer
from db.models import Image
from db.repository import ImageRepository


def run_infer_for_db_image(
    settings: Settings,
    repo: ImageRepository,
    row: Image,
    topk: int,
) -> dict:
    """对库中一条 Image 跑推理，返回 run_infer 同款 dict。"""
    path: Path = repo.abs_storage_path(row)
    if not path.is_file():
        raise FileNotFoundError(f"存储文件缺失: {path}")
    image_bgr = _read_bgr_from_upload_bytes(path.read_bytes())
    sam_path = path if row.image_kind == "full_face_selfie" else None
    return run_infer(
        settings,
        image_kind=row.image_kind,
        image_bgr=image_bgr,
        sam_source_path=sam_path,
        topk=topk,
    )
