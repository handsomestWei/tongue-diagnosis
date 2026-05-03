"""Ultralytics YOLO classify：规范舌图 BGR -> top-k。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def classify_topk_bgr(
    weights: Path,
    image_bgr: np.ndarray,
    *,
    topk: int = 3,
    device: str = "cpu",
    imgsz: int | None = 224,
) -> list[dict[str, Any]]:
    """返回 [{\"class\": str, \"score\": float}, ...] 按分数降序。"""
    import torch
    from ultralytics import YOLO

    if image_bgr.dtype != np.uint8 or image_bgr.ndim != 3:
        raise ValueError("image_bgr 须为 uint8 HxWx3 BGR")

    w = weights.expanduser().resolve()
    if not w.is_file():
        raise FileNotFoundError(f"权重不存在: {w}")

    model = YOLO(str(w))
    pred_kw: dict = dict(source=image_bgr, device=device or "cpu", verbose=False)
    if imgsz and imgsz > 0:
        pred_kw["imgsz"] = imgsz

    pred = model.predict(**pred_kw)
    if not pred:
        return []
    r = pred[0]
    if r.probs is None:
        return []

    probs = r.probs
    t = probs.data
    if not isinstance(t, torch.Tensor):
        t = torch.as_tensor(t)
    k = max(1, min(topk, int(t.numel())))
    idxs = t.argsort(descending=True)[:k]
    names = getattr(r, "names", None) or getattr(probs, "names", {}) or {}
    out: list[dict[str, Any]] = []
    for i in idxs:
        ci = int(i)
        name = names.get(ci, str(ci)) if isinstance(names, dict) else str(ci)
        out.append({"class": str(name), "score": float(t[ci])})
    return out
