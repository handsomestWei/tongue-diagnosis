"""编排：预处理（含可选 TongueSAM）+ YOLO classify top-k。"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from api.config import Settings
from core.infer_slots import acquire_infer_slot
from core.inference_yolo import classify_topk_bgr
from core.preprocess_classify import preprocess_for_classify
from core.sam_bridge import run_tonguesam_get_mask_box


def _read_bgr_from_upload_bytes(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("无法解码为图像")
    return bgr


def run_infer(
    settings: Settings,
    *,
    image_kind: str,
    image_bgr: np.ndarray,
    sam_source_path: Path | None,
    topk: int,
) -> dict[str, Any]:
    """
    :param sam_source_path: full_face 时若可复用磁盘路径调用 SAM，可避免临时文件
    :returns: demo, message, image_kind, topk(list), sam_called, sam_failed
    """
    tonguesam_root = Path(settings.tonguesam_root).resolve()

    with acquire_infer_slot():
        if image_kind == "full_face_selfie":
            cleanup_path: Path | None = None
            path_for_sam = sam_source_path
            if path_for_sam is None:
                fd, name = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                cleanup_path = Path(name)
                cv2.imwrite(str(cleanup_path), image_bgr)
                path_for_sam = cleanup_path
            try:

                def sam_box_provider():
                    return run_tonguesam_get_mask_box(
                        path_for_sam,
                        tonguesam_root,
                        timeout_sec=settings.infer_sam_timeout_sec,
                    )

                pre = preprocess_for_classify(
                    image_bgr,
                    image_kind,
                    sam_box_provider=sam_box_provider,
                    out_size=settings.infer_imgsz,
                )
            finally:
                if cleanup_path is not None:
                    cleanup_path.unlink(missing_ok=True)
        else:
            pre = preprocess_for_classify(
                image_bgr,
                image_kind,
                out_size=settings.infer_imgsz,
            )

    wraw = (settings.classify_weights_path or "").strip()
    if not wraw:
        k = max(1, min(topk, 10))
        demo_rank = [
            {"class": "淡红舌", "score": 0.42},
            {"class": "红舌", "score": 0.31},
            {"class": "淡白舌", "score": 0.12},
            {"class": "紫舌", "score": 0.08},
        ]
        return {
            "demo": True,
            "message": "未配置 CLASSIFY_WEIGHTS_PATH，返回演示 top-k",
            "image_kind": image_kind,
            "topk": demo_rank[:k],
            "sam_called": pre.sam_called,
            "sam_failed": pre.sam_failed,
        }

    wpath = Path(wraw).expanduser()
    if not wpath.is_file():
        raise FileNotFoundError(f"权重文件不存在: {wpath}")

    rankings = classify_topk_bgr(
        wpath,
        pre.tensor_bgr,
        topk=topk,
        device=settings.infer_device,
        imgsz=settings.infer_imgsz,
    )
    msg = "ok"
    if pre.detail:
        msg = pre.detail
    if pre.sam_failed:
        msg = (msg + "；" if msg != "ok" else "") + "SAM 异常已回退整图裁剪"

    return {
        "demo": False,
        "message": msg,
        "image_kind": image_kind,
        "topk": rankings,
        "sam_called": pre.sam_called,
        "sam_failed": pre.sam_failed,
    }


__all__ = ["run_infer", "_read_bgr_from_upload_bytes"]
