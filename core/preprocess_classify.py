"""按 image_kind 生成 YOLO classify 用规范舌图（BGR uint8）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

import numpy as np

from tongue_diag.roi.pipeline import pick_xyxy, process_one

ImageKind = Literal["full_face_selfie", "tongue_closeup"]

# full_face 时由 TongueSAM 桥接提供 mask 框（原图像素 xyxy）
SamBoxProvider = Callable[[], list[float]]


@dataclass
class PreprocessResult:
    """预处理结果。"""

    tensor_bgr: np.ndarray  # HWC BGR uint8，已 letterbox/resize
    sam_called: bool
    sam_failed: bool = False
    detail: str = ""


def _whole_image_xyxy(h: int, w: int) -> list[float]:
    return [0.0, 0.0, float(max(0, w - 1)), float(max(0, h - 1))]


def preprocess_for_classify(
    image_bgr: np.ndarray,
    image_kind: str,
    *,
    sam_box_provider: SamBoxProvider | None = None,
    margin: float = 0.12,
    out_size: int = 224,
    letterbox: bool = True,
    clahe: bool = True,
    unsharp: bool = False,
) -> PreprocessResult:
    """
    :param image_bgr: 原始图 BGR
    :param image_kind: full_face_selfie | tongue_closeup
    :param sam_box_provider: 仅 full_face 需要；应调用 TongueSAM 并返回 box_mask_xyxy（原图坐标）
    """
    if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("image_bgr 须为 HxWx3 BGR")
    h, w = image_bgr.shape[:2]

    if image_kind == "tongue_closeup":
        xyxy = _whole_image_xyxy(h, w)
        out = process_one(
            image_bgr,
            xyxy,
            margin=margin,
            out_size=out_size,
            letterbox=letterbox,
            clahe=clahe,
            unsharp=unsharp,
        )
        return PreprocessResult(tensor_bgr=out, sam_called=False)

    if image_kind != "full_face_selfie":
        raise ValueError(f"未知 image_kind: {image_kind!r}")

    if sam_box_provider is None:
        raise ValueError("full_face_selfie 须提供 sam_box_provider")

    sam_called = True
    try:
        xyxy = sam_box_provider()
    except Exception as e:
        xyxy = _whole_image_xyxy(h, w)
        return PreprocessResult(
            tensor_bgr=process_one(
                image_bgr,
                xyxy,
                margin=margin,
                out_size=out_size,
                letterbox=letterbox,
                clahe=clahe,
                unsharp=unsharp,
            ),
            sam_called=True,
            sam_failed=True,
            detail=str(e),
        )

    if xyxy is None or len(xyxy) != 4:
        xyxy = _whole_image_xyxy(h, w)
        return PreprocessResult(
            tensor_bgr=process_one(
                image_bgr,
                xyxy,
                margin=margin,
                out_size=out_size,
                letterbox=letterbox,
                clahe=clahe,
                unsharp=unsharp,
            ),
            sam_called=True,
            sam_failed=True,
            detail="未得到有效舌部框，已退回整图",
        )

    out = process_one(
        image_bgr,
        [float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])],
        margin=margin,
        out_size=out_size,
        letterbox=letterbox,
        clahe=clahe,
        unsharp=unsharp,
    )
    return PreprocessResult(tensor_bgr=out, sam_called=sam_called, sam_failed=False)
