"""Ultralytics YOLO classify 推理（支持 Top-K 打印）。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--weights",
        type=Path,
        required=True,
        help="训练得到的 best.pt",
    )
    p.add_argument("--source", type=str, required=True, help="图片路径或目录")
    p.add_argument("--device", type=str, default="")
    p.add_argument(
        "--topk",
        type=int,
        default=3,
        metavar="K",
        help="打印每图概率最高的前 K 类",
    )
    p.add_argument("--imgsz", type=int, default=0, help="0=使用模型默认/训练尺寸")
    args = p.parse_args()

    w = args.weights.expanduser().resolve()
    if not w.is_file():
        print(
            f"未找到权重文件: {w}\n"
            "提示：多次训练时目录常为 train2、train3，请检查 runs/classify/",
            file=sys.stderr,
        )
        sys.exit(1)

    import torch
    from ultralytics import YOLO

    model = YOLO(str(w))
    pred_kw: dict = dict(source=args.source, device=args.device or None, verbose=True)
    if args.imgsz and args.imgsz > 0:
        pred_kw["imgsz"] = args.imgsz
    pred = model.predict(**pred_kw)
    for r in pred:
        if r.probs is None:
            continue
        probs = r.probs
        t = probs.data
        if not isinstance(t, torch.Tensor):
            t = torch.as_tensor(t)
        k = max(1, min(args.topk, int(t.numel())))
        idxs = t.argsort(descending=True)[:k]
        parts = [f"{r.names[int(i)]} {float(t[i]):.4f}" for i in idxs]
        print(r.path, "->", " | ".join(parts))


if __name__ == "__main__":
    main()
