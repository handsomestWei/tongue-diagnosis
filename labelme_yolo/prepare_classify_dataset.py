"""
整理 YOLOv8 图像分类（classify）所需目录：train/类名/*、val/类名/*

两种来源（二选一子命令）：

1) from-7542e
   直接使用 7542e-main 按类别分文件夹的图像，按比例划分 train/val。

2) from-yolo-detect
   从 labelme2yolo 生成的 YOLODataset（images + labels + dataset.yaml）读取每张图的
   检测标签首行 class_id，映射 dataset.yaml 的 names，复制到 train/类名、val/类名。

示例：

  python prepare_classify_dataset.py from-7542e ^
    --src ..\\dataset\\7542e-main --out ..\\dataset\\tongue_cls_yolov8 --val-ratio 0.2

  python prepare_classify_dataset.py from-yolo-detect ^
    --dataset ..\\dataset\\7542e_labelme_flat\\YOLODataset --out ..\\dataset\\tongue_cls_from_yolo
"""
from __future__ import annotations

import argparse
import ast
import random
import re
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def _safe_dir_name(name: str) -> str:
    s = re.sub(r'[\\/:*?"<>|]+', "_", name.strip())
    s = re.sub(r"\s+", " ", s).strip().strip(".")
    return s or "class"


def _load_names_from_dataset_yaml(yaml_path: Path) -> List[str]:
    text = yaml_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("names:"):
            rest = line.split(":", 1)[1].strip()
            try:
                names = ast.literal_eval(rest)
            except (SyntaxError, ValueError) as e:
                raise ValueError(f"无法解析 dataset.yaml 中的 names 行: {line!r}") from e
            if not isinstance(names, list):
                raise ValueError("names 应为列表")
            return [str(x) for x in names]
    raise ValueError(f"未在 {yaml_path} 中找到 names: 行")


def _iter_images(folder: Path) -> List[Path]:
    out: List[Path] = []
    if not folder.is_dir():
        return out
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_EXT:
            out.append(p)
    return sorted(out)


def _split_list(items: List[Path], val_ratio: float, seed: int) -> Tuple[List[Path], List[Path]]:
    if not items:
        return [], []
    rng = random.Random(seed)
    idx = list(range(len(items)))
    rng.shuffle(idx)
    n_val = int(round(len(items) * val_ratio))
    n_val = max(0, min(n_val, len(items)))
    val_set = set(idx[:n_val])
    train = [items[i] for i in range(len(items)) if i not in val_set]
    val = [items[i] for i in range(len(items)) if i in val_set]
    return train, val


def cmd_from_7542e(args: argparse.Namespace) -> None:
    src: Path = args.src.resolve()
    out: Path = args.out.resolve()
    if not src.is_dir():
        raise SystemExit(f"源目录不存在: {src}")

    for split in ("train", "val"):
        d = out / split
        if d.exists() and args.clean:
            shutil.rmtree(d)
    out.mkdir(parents=True, exist_ok=True)

    total = 0
    for cls_dir in sorted(src.iterdir()):
        if not cls_dir.is_dir():
            continue
        imgs = _iter_images(cls_dir)
        if not imgs:
            print(f"[跳过] 无图像: {cls_dir}")
            continue
        train_imgs, val_imgs = _split_list(imgs, args.val_ratio, args.seed)
        cls_name = _safe_dir_name(cls_dir.name)

        for split_name, lst in (("train", train_imgs), ("val", val_imgs)):
            dest_cls = out / split_name / cls_name
            dest_cls.mkdir(parents=True, exist_ok=True)
            for p in lst:
                dest = dest_cls / p.name
                if dest.exists():
                    dest = dest_cls / f"{cls_dir.name}_{p.name}"
                if args.symlink:
                    try:
                        dest.symlink_to(p.resolve())
                    except OSError:
                        shutil.copy2(p, dest)
                else:
                    shutil.copy2(p, dest)
                total += 1
        print(f"{cls_dir.name}: train={len(train_imgs)} val={len(val_imgs)} -> {cls_name}")

    print(f"完成。共写入 {total} 个文件到 {out}（train/类名、val/类名）")


def _first_class_id_from_label(txt_path: Path) -> Optional[int]:
    if not txt_path.is_file():
        return None
    raw = txt_path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    first = raw.splitlines()[0].strip()
    if not first:
        return None
    parts = first.split()
    try:
        return int(float(parts[0]))
    except ValueError:
        return None


def cmd_from_yolo_detect(args: argparse.Namespace) -> None:
    ds: Path = args.dataset.resolve()
    out: Path = args.out.resolve()
    yaml_path = ds / "dataset.yaml"
    if not yaml_path.is_file():
        raise SystemExit(f"未找到 dataset.yaml: {yaml_path}")

    names = _load_names_from_dataset_yaml(yaml_path)
    nc = len(names)
    if nc == 0:
        raise SystemExit("names 为空")

    for split in ("train", "val"):
        d = out / split
        if d.exists() and args.clean:
            shutil.rmtree(d)
    out.mkdir(parents=True, exist_ok=True)

    img_root = ds / "images"
    lbl_root = ds / "labels"
    total = 0
    skipped = 0

    for split in ("train", "val"):
        idir = img_root / split
        ldir = lbl_root / split
        if not idir.is_dir():
            print(f"[警告] 无目录: {idir}")
            continue
        for img_path in _iter_images(idir):
            lbl_path = ldir / (img_path.stem + ".txt")
            cid = _first_class_id_from_label(lbl_path)
            if cid is None or cid < 0 or cid >= nc:
                skipped += 1
                continue
            cls_raw = names[cid]
            cls_name = _safe_dir_name(cls_raw)
            dest_dir = out / split / cls_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / img_path.name
            if dest.exists():
                dest = dest_dir / f"{img_path.stem}_{cid}{img_path.suffix.lower()}"
            if args.symlink:
                try:
                    dest.symlink_to(img_path.resolve())
                except OSError:
                    shutil.copy2(img_path, dest)
            else:
                shutil.copy2(img_path, dest)
            total += 1

    print(f"完成。复制/链接 {total} 个文件到 {out}；跳过 {skipped} 个（无标签或 class_id 无效）")
    print(f"类别数 {nc}；请使用: yolo classify train data={out} ...")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="准备 YOLOv8 classify 目录结构")
    sub = p.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("from-7542e", help="从 7542e-main 式「每类一子文件夹」划分 train/val")
    p1.add_argument("--src", type=Path, required=True, help="7542e-main 根目录")
    p1.add_argument("--out", type=Path, required=True, help="输出根目录（生成 train/、val/）")
    p1.add_argument("--val-ratio", type=float, default=0.2, help="验证集比例（每类内划分）")
    p1.add_argument("--seed", type=int, default=42)
    p1.add_argument("--clean", action="store_true", help="若输出下已有 train/val 则先删除")
    p1.add_argument("--symlink", action="store_true", help="尽量用符号链接（失败则回退复制）")
    p1.set_defaults(func=cmd_from_7542e)

    p2 = sub.add_parser("from-yolo-detect", help="从 YOLODataset 按 labels 首行 class_id 归类")
    p2.add_argument("--dataset", type=Path, required=True, help="YOLODataset 目录（含 dataset.yaml）")
    p2.add_argument("--out", type=Path, required=True, help="输出根目录")
    p2.add_argument("--clean", action="store_true")
    p2.add_argument("--symlink", action="store_true")
    p2.set_defaults(func=cmd_from_yolo_detect)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
