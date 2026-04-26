from __future__ import annotations

import argparse
from pathlib import Path

from tongue_diag.roi.pipeline import run_batch


def main() -> None:
    p = argparse.ArgumentParser(
        description="读取 SAM/TongueSAM 生成的 ROI JSON，裁剪/resize/增强后输出，供 YOLO 分类等使用。"
    )
    p.add_argument("--images_dir", type=Path, required=True, help="原始图片目录")
    p.add_argument("--roi_dir", type=Path, required=True, help="ROI JSON 目录")
    p.add_argument("--out_dir", type=Path, required=True, help="输出裁剪图目录")
    p.add_argument(
        "--box_source",
        choices=("auto", "mask", "yolox"),
        default="auto",
        help="auto=优先 box_mask_xyxy；mask / yolox 强制",
    )
    p.add_argument(
        "--margin",
        type=float,
        default=0.12,
        help="相对框宽高扩边；0=不扩边",
    )
    p.add_argument("--size", type=int, default=512, help="输出边长；0=不缩放")
    p.add_argument("--letterbox", action="store_true", help="保持比例并 pad 到 size×size")
    p.add_argument("--clahe", action="store_true", help="LAB CLAHE")
    p.add_argument("--unsharp", action="store_true", help="Unsharp 锐化")
    args = p.parse_args()

    out_size = None if args.size <= 0 else args.size
    n = run_batch(
        args.images_dir.resolve(),
        args.roi_dir.resolve(),
        args.out_dir.resolve(),
        box_source=args.box_source,  # type: ignore[arg-type]
        margin=args.margin,
        out_size=out_size,
        letterbox=args.letterbox,
        clahe=args.clahe,
        unsharp=args.unsharp,
    )
    print(f"Wrote {n} images to {args.out_dir}")


if __name__ == "__main__":
    main()
