"""CLI：准备 YOLOv8 classify 数据目录（from-7542e | from-yolo-detect）。"""
from __future__ import annotations

import argparse
from pathlib import Path

from tongue_diag.dataset.split_utils import (
    prepare_from_class_folders,
    prepare_from_yolo_detect,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="准备 YOLOv8 classify 目录结构")
    sub = p.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("from-7542e", help="从「每类一子文件夹」按比例划分 train/val")
    p1.add_argument("--src", type=Path, required=True)
    p1.add_argument("--out", type=Path, required=True)
    p1.add_argument("--val-ratio", type=float, default=0.2)
    p1.add_argument("--seed", type=int, default=42)
    p1.add_argument("--clean", action="store_true")
    p1.add_argument("--symlink", action="store_true")
    p1.set_defaults(func=_run_from_7542e)

    p2 = sub.add_parser("from-yolo-detect", help="从 YOLODataset 按检测标签首行 class_id 归类")
    p2.add_argument("--dataset", type=Path, required=True)
    p2.add_argument("--out", type=Path, required=True)
    p2.add_argument("--clean", action="store_true")
    p2.add_argument("--symlink", action="store_true")
    p2.set_defaults(func=_run_from_yolo)

    return p


def _run_from_7542e(args: argparse.Namespace) -> None:
    prepare_from_class_folders(
        args.src.resolve(),
        args.out.resolve(),
        val_ratio=args.val_ratio,
        seed=args.seed,
        clean=args.clean,
        symlink=args.symlink,
    )


def _run_from_yolo(args: argparse.Namespace) -> None:
    prepare_from_yolo_detect(
        args.dataset.resolve(),
        args.out.resolve(),
        clean=args.clean,
        symlink=args.symlink,
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
