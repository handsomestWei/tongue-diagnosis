from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Optional, Tuple

import cv2
import numpy as np

BoxSource = Literal["auto", "mask", "yolox"]


def load_roi_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_xyxy(record: dict[str, Any], source: BoxSource) -> Optional[list[float]]:
    if source == "yolox":
        return record.get("box_yolox_xyxy")
    if source == "mask":
        return record.get("box_mask_xyxy")
    m = record.get("box_mask_xyxy")
    if m is not None:
        return m
    return record.get("box_yolox_xyxy")


def expand_xyxy(
    xyxy: list[float], w: int, h: int, margin: float
) -> Tuple[int, int, int, int]:
    x0, y0, x1, y1 = xyxy
    bw = x1 - x0
    bh = y1 - y0
    cx = (x0 + x1) * 0.5
    cy = (y0 + y1) * 0.5
    bw2 = bw * (1.0 + margin)
    bh2 = bh * (1.0 + margin)
    nx0 = int(round(cx - bw2 * 0.5))
    ny0 = int(round(cy - bh2 * 0.5))
    nx1 = int(round(cx + bw2 * 0.5))
    ny1 = int(round(cy + bh2 * 0.5))
    nx0 = max(0, nx0)
    ny0 = max(0, ny0)
    nx1 = min(w - 1, nx1)
    ny1 = min(h - 1, ny1)
    if nx1 <= nx0 or ny1 <= ny0:
        return 0, 0, max(1, w - 1), max(1, h - 1)
    return nx0, ny0, nx1, ny1


def apply_clahe_bgr(img: np.ndarray, clip: float = 2.0, tile: int = 8) -> np.ndarray:
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tile, tile))
    l2 = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l2, a, b]), cv2.COLOR_LAB2BGR)


def unsharp_bgr(img: np.ndarray, sigma: float = 1.0, amount: float = 0.8) -> np.ndarray:
    blur = cv2.GaussianBlur(img, (0, 0), sigma)
    return cv2.addWeighted(img, 1.0 + amount, blur, -amount, 0)


def process_one(
    image_bgr: np.ndarray,
    xyxy: list[float],
    *,
    margin: float,
    out_size: Optional[int],
    letterbox: bool,
    clahe: bool,
    unsharp: bool,
) -> np.ndarray:
    h, w = image_bgr.shape[:2]
    x0, y0, x1, y1 = expand_xyxy(xyxy, w, h, margin)
    crop = image_bgr[y0 : y1 + 1, x0 : x1 + 1].copy()
    if crop.size == 0:
        crop = image_bgr.copy()

    if clahe:
        crop = apply_clahe_bgr(crop)
    if unsharp:
        crop = unsharp_bgr(crop)

    if out_size is not None and out_size > 0:
        ch, cw = crop.shape[:2]
        if letterbox:
            scale = min(out_size / cw, out_size / ch)
            nw = max(1, int(round(cw * scale)))
            nh = max(1, int(round(ch * scale)))
            resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
            canvas = np.zeros((out_size, out_size, 3), dtype=np.uint8)
            pad_x = (out_size - nw) // 2
            pad_y = (out_size - nh) // 2
            canvas[pad_y : pad_y + nh, pad_x : pad_x + nw] = resized
            crop = canvas
        else:
            crop = cv2.resize(crop, (out_size, out_size), interpolation=cv2.INTER_AREA)

    return crop


def run_batch(
    images_dir: Path,
    roi_dir: Path,
    out_dir: Path,
    *,
    box_source: BoxSource = "auto",
    margin: float = 0.12,
    out_size: Optional[int] = 512,
    letterbox: bool = False,
    clahe: bool = False,
    unsharp: bool = False,
    ext: str = ".png",
) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    n_ok = 0
    for jp in sorted(roi_dir.glob("*.json")):
        rec = load_roi_json(jp)
        name = rec.get("image_file")
        if not name:
            continue
        img_path = images_dir / name
        if not img_path.is_file():
            continue
        xyxy = pick_xyxy(rec, box_source)
        if xyxy is None:
            continue
        bgr = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if bgr is None:
            continue
        out = process_one(
            bgr,
            xyxy,
            margin=margin,
            out_size=out_size,
            letterbox=letterbox,
            clahe=clahe,
            unsharp=unsharp,
        )
        stem = jp.stem
        cv2.imwrite(str(out_dir / f"{stem}{ext}"), out)
        n_ok += 1
    return n_ok
