"""生成 YOLOv8 classify 目录：train/类名/*、val/类名/*。"""
from __future__ import annotations

import ast
import random
import re
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def safe_dir_name(name: str) -> str:
    s = re.sub(r'[\\/:*?"<>|]+', "_", name.strip())
    s = re.sub(r"\s+", " ", s).strip().strip(".")
    return s or "class"


def iter_images(folder: Path) -> List[Path]:
    out: List[Path] = []
    if not folder.is_dir():
        return out
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_EXT:
            out.append(p)
    return sorted(out)


def split_list(items: List[Path], val_ratio: float, seed: int) -> Tuple[List[Path], List[Path]]:
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


def prepare_from_class_folders(
    src: Path,
    out: Path,
    *,
    val_ratio: float = 0.2,
    seed: int = 42,
    clean: bool = False,
    symlink: bool = False,
) -> int:
    """每类一子文件夹，按类内比例划分 train/val。返回写入文件数。"""
    if not src.is_dir():
        raise SystemExit(f"源目录不存在: {src}")
    for split in ("train", "val"):
        d = out / split
        if d.exists() and clean:
            shutil.rmtree(d)
    out.mkdir(parents=True, exist_ok=True)
    total = 0
    for cls_dir in sorted(src.iterdir()):
        if not cls_dir.is_dir():
            continue
        imgs = iter_images(cls_dir)
        if not imgs:
            print(f"[跳过] 无图像: {cls_dir}")
            continue
        train_imgs, val_imgs = split_list(imgs, val_ratio, seed)
        cls_name = safe_dir_name(cls_dir.name)
        for split_name, lst in (("train", train_imgs), ("val", val_imgs)):
            dest_cls = out / split_name / cls_name
            dest_cls.mkdir(parents=True, exist_ok=True)
            for p in lst:
                dest = dest_cls / p.name
                if dest.exists():
                    dest = dest_cls / f"{cls_dir.name}_{p.name}"
                if symlink:
                    try:
                        dest.symlink_to(p.resolve())
                    except OSError:
                        shutil.copy2(p, dest)
                else:
                    shutil.copy2(p, dest)
                total += 1
        print(f"{cls_dir.name}: train={len(train_imgs)} val={len(val_imgs)} -> {cls_name}")
    print(f"完成。共写入 {total} 个文件到 {out}")
    return total


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


def prepare_from_yolo_detect(
    dataset: Path,
    out: Path,
    *,
    clean: bool = False,
    symlink: bool = False,
) -> int:
    """从 YOLODataset 按 labels 首行 class_id 与 dataset.yaml 的 names 归类到 train/val/类名。"""
    yaml_path = dataset / "dataset.yaml"
    if not yaml_path.is_file():
        raise SystemExit(f"未找到 dataset.yaml: {yaml_path}")
    names = _load_names_from_dataset_yaml(yaml_path)
    nc = len(names)
    if nc == 0:
        raise SystemExit("names 为空")
    for split in ("train", "val"):
        d = out / split
        if d.exists() and clean:
            shutil.rmtree(d)
    out.mkdir(parents=True, exist_ok=True)
    img_root = dataset / "images"
    lbl_root = dataset / "labels"
    total = 0
    skipped = 0
    for split in ("train", "val"):
        idir = img_root / split
        ldir = lbl_root / split
        if not idir.is_dir():
            print(f"[警告] 无目录: {idir}")
            continue
        for img_path in iter_images(idir):
            lbl_path = ldir / (img_path.stem + ".txt")
            cid = _first_class_id_from_label(lbl_path)
            if cid is None or cid < 0 or cid >= nc:
                skipped += 1
                continue
            cls_raw = names[cid]
            cls_name = safe_dir_name(cls_raw)
            dest_dir = out / split / cls_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / img_path.name
            if dest.exists():
                dest = dest_dir / f"{img_path.stem}_{cid}{img_path.suffix.lower()}"
            if symlink:
                try:
                    dest.symlink_to(img_path.resolve())
                except OSError:
                    shutil.copy2(img_path, dest)
            else:
                shutil.copy2(img_path, dest)
            total += 1
    print(f"完成。复制/链接 {total} 个；跳过 {skipped} 个")
    return total
