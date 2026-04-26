"""
仅「按类文件夹的原始整图」+ TongueSAM（SAM+提示头）自动裁舌，再划 train/val，
得到 YOLOv8 classify 可直接 `data=` 的目录。无需 LabelMe、无需检测框标注。

依赖：本机已按 TongueSAM 说明配置好权重，且 `predict.py` 可从仓库根运行。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from tongue_diag.dataset.split_utils import (
    iter_images,
    safe_dir_name,
    prepare_from_class_folders,
)
from tongue_diag.roi.pipeline import run_batch

MANIFEST = "tongue_diag_sam_manifest.json"


def default_tongue_sam_root() -> Path:
    """本仓库内整合后的 TongueSAM 根目录（与可安装包 `tongue_diag` 并列的 `tongue_sam/`）。"""
    return Path(__file__).resolve().parent.parent.parent / "tongue_sam"


def _clear_dir_contents(d: Path) -> None:
    if not d.is_dir():
        d.mkdir(parents=True, exist_ok=True)
        return
    for child in d.iterdir():
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def build_manifest(
    src_root: Path,
) -> tuple[list[tuple[str, Path, str]], dict[str, dict[str, Any]]]:
    """
    为每张图分配全局唯一 stem：g{ci:02d}_i{ii:06d}（无扩展名用于 json/png）。
    返回：平面列表 (class_label, 源图路径, stem)；与 manifest 索引 dict[stem] -> meta。
    """
    class_dirs = sorted([d for d in src_root.iterdir() if d.is_dir()])
    if not class_dirs:
        raise SystemExit(f"源目录下无类子文件夹: {src_root}")
    items: list[tuple[str, Path, str]] = []
    meta: dict[str, dict[str, Any]] = {}
    global_i = 0
    for ci, cls_dir in enumerate(class_dirs):
        label = cls_dir.name
        for img in iter_images(cls_dir):
            stem = f"g{ci:02d}_i{global_i:06d}"
            global_i += 1
            items.append((label, img, stem))
            meta[stem] = {
                "class": label,
                "class_safe": safe_dir_name(label),
                "src": str(img.resolve()),
            }
    if not items:
        raise SystemExit("未找到任何图像；请检查类文件夹内是否含 jpg/png 等。")
    return items, meta


def run_tonguesam_predict(tonguesam_root: Path) -> None:
    pred = tonguesam_root / "predict.py"
    if not pred.is_file():
        raise SystemExit(f"未找到 TongueSAM predict.py: {pred}")
    r = subprocess.run(
        [sys.executable, str(pred)],
        cwd=str(tonguesam_root.resolve()),
        check=False,
    )
    if r.returncode != 0:
        raise SystemExit(
            f"TongueSAM predict 退出码 {r.returncode}。请检查 GPU、权重与 data/test_in 图片。"
        )


def pipeline(
    src_root: Path,
    out_cls_root: Path,
    tonguesam_root: Path,
    work_dir: Path,
    *,
    val_ratio: float,
    seed: int,
    clean_sam_io: bool,
    clean_work: bool,
    skip_sam: bool,
    box_source: str,
    margin: float,
    size: int,
    letterbox: bool,
    clahe: bool,
    unsharp: bool,
) -> None:
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    if clean_work and work_dir.exists():
        for p in work_dir.iterdir():
            if p.is_file() or p.is_dir():
                if p.is_file():
                    p.unlink()
                else:
                    shutil.rmtree(p)

    ts_in = tonguesam_root / "data" / "test_in"
    ts_roi = tonguesam_root / "data" / "test_roi"
    ts_out = tonguesam_root / "data" / "test_out"
    for d in (ts_in, ts_roi, ts_out):
        d.parent.mkdir(parents=True, exist_ok=True)

    mpath = work_dir / MANIFEST
    if skip_sam:
        if not mpath.is_file():
            raise SystemExit(
                f"--skip-sam 需要已存在 {mpath}；请先成功跑通一次以生成 manifest，或去掉 --skip-sam"
            )
        meta = json.loads(mpath.read_text(encoding="utf-8"))
    else:
        items, meta = build_manifest(src_root)
        mpath.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if not skip_sam:
        if clean_sam_io:
            _clear_dir_contents(ts_in)
            _clear_dir_contents(ts_roi)
            _clear_dir_contents(ts_out)
        for _label, img_path, stem in items:
            ext = img_path.suffix.lower() or ".jpg"
            dest = ts_in / f"{stem}{ext}"
            shutil.copy2(img_path, dest)

        run_tonguesam_predict(tonguesam_root)
    else:
        print("skip-sam: 使用已有 test_in / test_roi，请保证与 manifest 中 stem 一致。")

    flat = work_dir / "flat_crops"
    flat.mkdir(parents=True, exist_ok=True)
    out_size = None if size <= 0 else size
    n = run_batch(
        ts_in.resolve(),
        ts_roi.resolve(),
        flat.resolve(),
        box_source=box_source,  # type: ignore[arg-type]
        margin=margin,
        out_size=out_size,
        letterbox=letterbox,
        clahe=clahe,
        unsharp=unsharp,
    )
    print(f"ROI 裁剪完成，写出 {n} 张到 {flat}")
    if n == 0 and not skip_sam:
        print(
            "警告：未得到任何裁切图。请检查 TongueSAM 是否写出 test_roi/*.json 且与 test_in 文件名对应。",
            file=sys.stderr,
        )

    by_class = work_dir / "by_class"
    if by_class.exists():
        shutil.rmtree(by_class)
    by_class.mkdir(parents=True, exist_ok=True)
    missing = 0
    for stem, m in meta.items():
        png = flat / f"{stem}.png"
        if not png.is_file():
            missing += 1
            continue
        sub = by_class / m["class_safe"]
        sub.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png, sub / f"{stem}.png")
    if missing:
        print(f"提示：{missing} 张在 SAM/ROI 阶段无输出，未进入 by_class", file=sys.stderr)

    out_cls_root = out_cls_root.resolve()
    prepare_from_class_folders(
        by_class,
        out_cls_root,
        val_ratio=val_ratio,
        seed=seed,
        clean=True,
        symlink=False,
    )
    print(f"完成。YOLO classify 数据根目录: {out_cls_root}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="仅分类文件夹原始整图 + TongueSAM 裁舌 -> train/val 分类数据集（无 LabelMe/检测标）"
    )
    p.add_argument(
        "--src",
        type=Path,
        required=True,
        help="源：每类一子文件夹，内含 jpg/png 整图",
    )
    p.add_argument(
        "--out",
        type=Path,
        required=True,
        help="输出 YOLO classify 数据根（生成 train/、val/）",
    )
    p.add_argument(
        "--tonguesam-root",
        type=Path,
        default=None,
        help="TongueSAM 根目录（含 predict.py、pretrained_model/）；默认本仓库的 tongue_sam/",
    )
    p.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="中间文件目录；默认 {out}../.td_sam_work",
    )
    p.add_argument("--val-ratio", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--clean-sam-io",
        action="store_true",
        help="运行前清空 TongueSAM 的 data/test_in、test_roi、test_out",
    )
    p.add_argument(
        "--clean-work",
        action="store_true",
        help="清空中 work-dir 再开始",
    )
    p.add_argument(
        "--skip-sam",
        action="store_true",
        help="不复制图、不跑 predict；需已有与 manifest 同 stem 的 test_in+test_roi",
    )
    p.add_argument(
        "--box_source",
        choices=("auto", "mask", "yolox"),
        default="auto",
    )
    p.add_argument("--margin", type=float, default=0.0, help="裁舌扩边；0=不扩边")
    p.add_argument("--size", type=int, default=224, help="输出边长，0=不缩放")
    p.add_argument("--letterbox", action="store_true")
    p.add_argument("--clahe", action="store_true")
    p.add_argument("--unsharp", action="store_true")
    args = p.parse_args()

    work = args.work_dir
    if work is None:
        work = args.out.parent / f"{args.out.name}_work"

    ts_root = args.tonguesam_root or default_tongue_sam_root()
    pipeline(
        src_root=args.src.resolve(),
        out_cls_root=args.out.resolve(),
        tonguesam_root=ts_root.resolve(),
        work_dir=work.resolve(),
        val_ratio=args.val_ratio,
        seed=args.seed,
        clean_sam_io=args.clean_sam_io,
        clean_work=args.clean_work,
        skip_sam=args.skip_sam,
        box_source=args.box_source,
        margin=args.margin,
        size=args.size,
        letterbox=args.letterbox,
        clahe=args.clahe,
        unsharp=args.unsharp,
    )


if __name__ == "__main__":
    main()
