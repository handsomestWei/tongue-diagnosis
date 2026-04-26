"""Ultralytics YOLO 图像分类训练。"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="YOLO classify train (Ultralytics)")
    p.add_argument("--data", type=Path, required=True, help="数据集根（含 train/ 与 val/）")
    p.add_argument("--model", type=str, default="yolov8n-cls.pt", help="预训练权重名或路径")
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--imgsz", type=int, default=224)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--device", type=str, default="", help="留空自动；或 cpu / 0 / 0,1")
    args = p.parse_args()

    from ultralytics import YOLO

    data = str(args.data.resolve())
    model = YOLO(args.model)
    kwargs: dict = dict(data=data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch)
    if args.device:
        kwargs["device"] = args.device
    model.train(**kwargs)


if __name__ == "__main__":
    main()
