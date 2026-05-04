"""从数据库导出 YOLO classify 目录（与推理共用 preprocess_for_classify）。"""
from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import Settings
from core.preprocess_classify import preprocess_for_classify
from core.sam_bridge import run_tonguesam_get_mask_box
from db.models import Correction, Image, Label, Prediction


def _safe_class_dir(name: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", name.strip())
    return s[:120] if s else "unknown"


@dataclass
class ExportStats:
    total_exported: int = 0
    n_train: int = 0
    n_val: int = 0
    by_kind: dict[str, int] = field(default_factory=dict)
    sam_called: int = 0
    sam_failed: int = 0


def export_yolo_classify_from_db(
    db: Session,
    settings: Settings,
    *,
    out_root: Path,
    val_ratio: float = 0.2,
    seed: int = 42,
    margin: float = 0.12,
    letterbox: bool = True,
    clahe: bool = True,
    unsharp: bool = False,
    update_derived_paths: bool = True,
    imgsz: int | None = None,
    selection: str = "all_manual",
    merge_base_manual: bool = False,
) -> tuple[Path, ExportStats, dict[str, Any]]:
    """
    导出带 **人工标注**（Label.source == manual）的图片为 YOLO classify 目录。

    ``selection``:
    - ``all_manual``: 所有带 manual 标注的图（默认全量训练）
    - ``corrections_flagged``: 仅 ``corrections.include_in_next_train == True`` 对应图片
      （纠错页勾选「纳入再训练」）
    - ``corrections_only``: 同上（别名）

    ``merge_base_manual``: 为 True 时，在增量训练中将 **全量 manual** 与 **勾选纠错样本** 合并导出
    （适用于 ``corrections_*`` 选择策略）。

    返回：(数据集根目录 out_root, 统计, meta dict 写入 TrainJob)
    """
    out_root = out_root.resolve()
    train_dir = out_root / "train"
    val_dir = out_root / "val"
    for d in (train_dir, val_dir):
        d.mkdir(parents=True, exist_ok=True)

    tonguesam_root = Path(settings.tonguesam_root).resolve()
    storage_root = Path(settings.storage_root).resolve()
    out_sz = int(imgsz) if imgsz and imgsz > 0 else int(settings.infer_imgsz)

    sel = (selection or "all_manual").strip().lower()
    if sel in ("corrections_only",):
        sel = "corrections_flagged"
    if sel not in ("all_manual", "corrections_flagged"):
        raise ValueError(f"不支持的导出选择策略: {selection}")

    # 每张图仅取一条 manual 标注（有多条时取 id 最大者）
    images = db.scalars(
        select(Image)
        .join(Label, Label.image_id == Image.id)
        .where(Label.source == "manual")
        .distinct()
    ).all()
    def _latest_flagged_correct_class(image_id: int) -> str | None:
        return db.scalar(
            select(Correction.correct_class)
            .join(Prediction, Prediction.id == Correction.prediction_id)
            .where(
                Prediction.image_id == image_id,
                Correction.include_in_next_train.is_(True),
            )
            .order_by(Correction.id.desc())
            .limit(1)
        )

    image_to_label: dict[int, str] = {}

    if sel == "corrections_flagged":
        correction_image_ids = set(
            db.scalars(
                select(Prediction.image_id)
                .join(Correction, Correction.prediction_id == Prediction.id)
                .where(Correction.include_in_next_train.is_(True))
            ).all()
        )
        if merge_base_manual:
            for im in images:
                lbl = db.scalar(
                    select(Label)
                    .where(Label.image_id == im.id, Label.source == "manual")
                    .order_by(Label.id.desc())
                    .limit(1)
                )
                if lbl:
                    image_to_label[im.id] = lbl.class_name
            for iid in correction_image_ids:
                cc = _latest_flagged_correct_class(iid)
                if cc:
                    image_to_label[iid] = cc
        else:
            for iid in correction_image_ids:
                cc = _latest_flagged_correct_class(iid)
                if cc:
                    image_to_label[iid] = cc
    else:
        for im in images:
            lbl = db.scalar(
                select(Label)
                .where(Label.image_id == im.id, Label.source == "manual")
                .order_by(Label.id.desc())
                .limit(1)
            )
            if lbl:
                image_to_label[im.id] = lbl.class_name

    if not image_to_label:
        if sel == "corrections_flagged":
            raise ValueError("没有勾选「纳入再训练」的纠错样本，无法导出增量数据集")
        raise ValueError("没有带人工标注（manual）的图片，无法导出训练集")

    ordered_ids = sorted(image_to_label.keys())
    images = db.scalars(select(Image).where(Image.id.in_(ordered_ids))).all()
    id_order = {i: n for n, i in enumerate(ordered_ids)}
    images.sort(key=lambda r: id_order.get(r.id, 10**9))

    by_class: dict[str, list[Image]] = {}
    for im in images:
        if im.id not in image_to_label:
            continue
        cls_safe = _safe_class_dir(image_to_label[im.id])
        by_class.setdefault(cls_safe, []).append(im)

    rng = random.Random(seed)
    stats = ExportStats()
    meta_images: list[dict[str, Any]] = []

    for cls_safe, items in by_class.items():
        rng.shuffle(items)
        n_val = int(round(len(items) * val_ratio))
        for i, img_row in enumerate(items):
            class_name = image_to_label[img_row.id]
            split_dir = val_dir if i < n_val else train_dir
            cls_out = split_dir / cls_safe
            cls_out.mkdir(parents=True, exist_ok=True)

            abs_img = storage_root / img_row.storage_path.replace("\\", "/")
            if not abs_img.is_file():
                continue

            bgr = cv2.imread(str(abs_img), cv2.IMREAD_COLOR)
            if bgr is None:
                continue

            stats.by_kind[img_row.image_kind] = stats.by_kind.get(img_row.image_kind, 0) + 1

            if img_row.image_kind == "full_face_selfie":

                def sam_box_provider():
                    return run_tonguesam_get_mask_box(abs_img, tonguesam_root, timeout_sec=settings.infer_sam_timeout_sec)

                pre = preprocess_for_classify(
                    bgr,
                    img_row.image_kind,
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
                    img_row.image_kind,
                    margin=margin,
                    out_size=out_sz,
                    letterbox=letterbox,
                    clahe=clahe,
                    unsharp=unsharp,
                )

            if pre.sam_called:
                stats.sam_called += 1
            if pre.sam_failed:
                stats.sam_failed += 1

            stem = (img_row.sha256 or hashlib.sha256(str(img_row.id).encode()).hexdigest())[:16]
            fname = f"{stem}.png"
            out_path = cls_out / fname
            cv2.imwrite(str(out_path), pre.tensor_bgr)

            if update_derived_paths:
                rel = str((Path("projects") / str(img_row.project_id) / "derived" / fname).as_posix())
                der_abs = storage_root / rel
                der_abs.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(der_abs), pre.tensor_bgr)
                img_row.derived_tongue_path = rel
                db.add(img_row)

            if split_dir == val_dir:
                stats.n_val += 1
            else:
                stats.n_train += 1
            stats.total_exported += 1
            meta_images.append(
                {
                    "image_id": img_row.id,
                    "class": class_name,
                    "image_kind": img_row.image_kind,
                    "split": "val" if split_dir == val_dir else "train",
                    "sam_failed": pre.sam_failed,
                }
            )

    db.commit()

    summary = {
        "export_root": str(out_root),
        "val_ratio": val_ratio,
        "seed": seed,
        "imgsz": out_sz,
        "margin": margin,
        "letterbox": letterbox,
        "clahe": clahe,
        "unsharp": unsharp,
        "selection": sel,
        "merge_base_manual": bool(merge_base_manual),
        "stats": {
            "total_exported": stats.total_exported,
            "n_train": stats.n_train,
            "n_val": stats.n_val,
            "by_image_kind": stats.by_kind,
            "sam_called": stats.sam_called,
            "sam_failed": stats.sam_failed,
        },
        "images": meta_images[:500],
    }
    (out_root / "export_meta.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_root, stats, summary
