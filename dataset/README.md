# 数据集（本地存放）

本目录用于在**本机**放置下载、解压后的实验数据。默认**不**将大文件提交到 Git（见仓库根目录 `.gitignore`）；仅需随仓说明时可保留本 `README.md`。

## 与仓库脚本的配合

- 常见目录约定（可改名）：

  - `7542e-main/`：按**类别**分子文件夹存放的舌象/LabelMe 等（与 [`labelme_yolo/7542e转YOLOv8-使用说明.md`](../labelme_yolo/7542e转YOLOv8-使用说明.md) 中的「例」一致）；
  - 扁平化/转换后的中间目录可自行命名，如 `labelme_flat/`、`YOLODataset/` 等，同样建议放在本目录下，便于与相对路径、文档示例对齐。

- 在 **`labelme_yolo/`** 下按 `7542e转YOLOv8-使用说明.md` 将 LabelMe 转为 YOLO 检测/分割格式时，可将 `--src` / `--dst` 指向本目录下的子路径；也可在仓库根使用 `python labelme_yolo/…` 时传入 `dataset/…` 形式的路径。

- **整图分类**数据准备见主包命令 `td-prepare-dataset`（`tongue_diag/dataset/prepare`），`from-7542e` 子命令仍表示「**每类一子文件夹**」式数据源，不特指固有名 `7542e-main`（目录名可自取）。

## 数据与许可链接（供检索）

| 资源 | 说明 |
|------|------|
| [open-source-toolkit/7542e（GitCode）](https://gitcode.com/open-source-toolkit/7542e) | 舌苔/舌象相关公开资源与下载入口的常用索引之一（**以页面与压缩包内许可说明为准**）。 |
| [rooneysh/Labelme2YOLO](https://github.com/rooneysh/Labelme2YOLO) | LabelMe → YOLO 格式转换；本仓 `labelme_yolo/labelme2yolo.py` 承继其能力。 |
| [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) | 检测/分割/分类等训练与推理。 |

> 各数据集、权重与商业使用条件以**发布方**页面为准；本仓库不托管原始数据，仅提供工具链与说明。
