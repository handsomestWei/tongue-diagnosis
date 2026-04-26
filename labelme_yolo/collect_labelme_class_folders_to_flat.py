"""
将「每类一子目录 / 内含 *.json」的 LabelMe 标注复制到**单一**目录，
供 `labelme2yolo.py` 使用（该脚本默认只读取 `json_dir` 根下的 `.json`）。

适用于任意**按类分文件夹**的 LabelMe 项目，不绑定某一固定数据集名。

用法（在 `labelme_yolo` 下或从仓库根指定脚本路径）:
  python collect_labelme_class_folders_to_flat.py ^
    --src "e:/.../dataset/my_project_by_class" ^
    --dst "e:/.../dataset/my_labelme_flat"

复制规则：目标文件名 = 安全化后的「父文件夹名」+ "__" + 原 json 文件名，避免不同类下同 basename 冲突。
json 内 `imageData` 仍保留，`labelme2yolo` 会从内嵌图写出对应图片。
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
    p = argparse.ArgumentParser(
        description="将每类一子目录中的 LabelMe .json 汇总到单目录，供 labelme2yolo 使用。"
    )
    p.add_argument(
        "--src",
        type=Path,
        required=True,
        help="根目录：其下每个子目录代表一类，内含 .json。",
    )
    p.add_argument(
        "--dst",
        type=Path,
        required=True,
        help="输出目录（将创建），所有 json 平铺在此。",
    )
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
