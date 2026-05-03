"""根据当前 image_kind 重新生成规范舌图并写入 derived_tongue_path。"""
from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
from sqlalchemy.orm import Session

from api.config import Settings
from core.preprocess_classify import preprocess_for_classify
from core.sam_bridge import run_tonguesam_get_mask_box
from db.models import Image


def regenerate_derived_for_image(
    db: Session,
    settings: Settings,
    row: Image,
    *,
    margin: float = 0.12,
    letterbox: bool = True,
    clahe: bool = True,
    unsharp: bool = False,
) -> str:
    """
    读取库内原图，按 ``image_kind`` 预处理后写入
    ``storage_root/projects/{project_id}/derived/{stem}.png``，更新 ``row.derived_tongue_path`` 并 ``commit``。
    """
    storage_root = Path(settings.storage_root).resolve()
    abs_img = storage_root / row.storage_path.replace("\\", "/")
    if not abs_img.is_file():
        raise FileNotFoundError(f"原图缺失: {abs_img}")

    bgr = cv2.imread(str(abs_img), cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("无法解码原图")

    tonguesam_root = Path(settings.tonguesam_root).resolve()
    out_sz = int(settings.infer_imgsz)

    if row.image_kind == "full_face_selfie":

        def sam_box_provider():
            return run_tonguesam_get_mask_box(
                abs_img, tonguesam_root, timeout_sec=settings.infer_sam_timeout_sec
            )

        pre = preprocess_for_classify(
            bgr,
            row.image_kind,
            sam_box_provider=sam_box_provider,
            margin=margin,
            out_size=out_sz,
            letterbox=letterbox,
            clahe=clahe,
            unsharp=unsharp,
        )
    else:
        pre = preprocess_for_classify(
            bgr,
            row.image_kind,
            margin=margin,
            out_size=out_sz,
            letterbox=letterbox,
            clahe=clahe,
            unsharp=unsharp,
        )

    stem = (row.sha256 or hashlib.sha256(str(row.id).encode()).hexdigest())[:16]
    fname = f"{stem}.png"
    rel = str((Path("projects") / str(row.project_id) / "derived" / fname).as_posix())
    der_abs = storage_root / rel
    der_abs.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(der_abs), pre.tensor_bgr)
    row.derived_tongue_path = rel
    db.add(row)
    db.commit()
    return rel


__all__ = ["regenerate_derived_for_image"]
