"""单图 TongueSAM：通过子进程运行 tongue_sam/predict.py，读取 test_roi/*.json。"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from tongue_diag.roi.pipeline import load_roi_json, pick_xyxy

from core.infer_slots import acquire_sam_slot

log = logging.getLogger(__name__)


def _clear_dir_files(d: Path) -> None:
    if not d.is_dir():
        d.mkdir(parents=True, exist_ok=True)
        return
    for f in d.iterdir():
        if f.is_file():
            f.unlink()


def run_tonguesam_get_mask_box(
    image_path: Path,
    tonguesam_root: Path,
    *,
    timeout_sec: int = 600,
) -> list[float]:
    """
    将单图送入 TongueSAM，返回原图像素空间的 box_mask_xyxy（若不可用则尝试 yolox）。
    """
    tonguesam_root = tonguesam_root.resolve()
    pred = tonguesam_root / "predict.py"
    if not pred.is_file():
        raise FileNotFoundError(f"未找到 TongueSAM: {pred}")

    ts_in = tonguesam_root / "data" / "test_in"
    ts_roi = tonguesam_root / "data" / "test_roi"
    ts_out = tonguesam_root / "data" / "test_out"
    for d in (ts_in, ts_roi, ts_out):
        d.mkdir(parents=True, exist_ok=True)

    _clear_dir_files(ts_in)
    _clear_dir_files(ts_roi)

    stem = f"api_{uuid.uuid4().hex[:12]}"
    ext = image_path.suffix if image_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"} else ".jpg"
    dest = ts_in / f"{stem}{ext}"
    shutil.copy2(image_path, dest)

    try:
        with acquire_sam_slot():
            env = os.environ.copy()
            # API 路径无需写可视化 PNG，加速并减少 IO
            env.setdefault("TONGUESAM_WRITE_VISUAL", "0")
            r = subprocess.run(
                [sys.executable, str(pred)],
                cwd=str(tonguesam_root),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
                env=env,
            )
        if r.returncode != 0:
            log.warning("TongueSAM exit %s: %s", r.returncode, (r.stderr or "")[:500])
            raise RuntimeError(f"TongueSAM 退出码 {r.returncode}")
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("TongueSAM 执行超时") from e

    roi_path = ts_roi / f"{stem}.json"
    if not roi_path.is_file():
        raise RuntimeError(f"未生成 ROI JSON: {roi_path}")

    rec = load_roi_json(roi_path)
    xyxy = pick_xyxy(rec, "auto")
    if xyxy is None:
        raise RuntimeError("ROI JSON 中无可用 box")
    return [float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])]
