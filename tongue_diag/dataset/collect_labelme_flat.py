"""
将按「类别文件夹 / *.json」存放的 LabelMe 复制到单目录，供 labelme2yolo 使用。
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


def safe_part(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "cls"


def main() -> None:
    p = argparse.ArgumentParser(description="展平「每类一子目录」的 LabelMe json 到单目录。")
    p.add_argument("--src", type=Path, required=True)
    p.add_argument("--dst", type=Path, required=True)
    args = p.parse_args()
    src: Path = args.src.resolve()
    dst: Path = args.dst.resolve()
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for cls_dir in sorted(src.iterdir()):
        if not cls_dir.is_dir():
            continue
        cls_key = safe_part(cls_dir.name)
        for jf in sorted(cls_dir.glob("*.json")):
            out_name = f"{cls_key}__{jf.name}"
            shutil.copy2(jf, dst / out_name)
            n += 1
    print(f"Copied {n} json files to {dst}")


if __name__ == "__main__":
    main()
