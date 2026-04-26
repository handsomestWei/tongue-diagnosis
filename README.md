# tongue-diagnosis

**命名说明**：目录/发布名为 `tongue-diagnosis`；可安装包目录为 **`tongue_diag/`**，`import` 使用 **`tongue_diag.*`**，与同仓的 `tongue_sam/`、`labelme_yolo/` 区分，也避免与项目名在字面上完全重复。

舌象相关 **Python 工具包**：ROI 裁剪（与 SAM JSON 配合）、**YOLOv8 分类** 训练/推理、分类数据准备，以及 **「仅按类文件夹的整图 + TongueSAM 自动裁舌」→ YOLO classify 数据目录** 的流水线。

## 环境

- **Python 3.10+**；推荐在仓库根目录使用虚拟环境 **`.venv`**（可从原 `TongueSAM` 下 `.venv310` 整目录重命名/迁移到根目录，统一在本环境中安装依赖与可编辑包）。
- 主包安装：在激活 `.venv` 后于仓库根执行 `pip install -e .`。
- 核心依赖见 `pyproject.toml`；`requirements.txt` 为与主包 `dependencies` 一致的简要列表。

### 与 TongueSAM 子工程

- 舌部分割与推理代码位于 **`tongue_sam/`**（原上游 TongueSAM 工程，已收拢到本仓库根目录下）。
- TongueSAM 另需 `segment_anything`、monai 等，详见 **`tongue_sam/README.md`**；在已含上述库的根目录 **`.venv`** 中，可直接在 `tongue_sam/` 下用 `python predict.py` 或依赖 **`td-prep-sam-cls`**（子进程调用 `tongue_sam/predict.py`）。

### 与 LabelMe → YOLO 脚本

- **`labelme_yolo/`**：原 `rooneysh-Labelme2YOLO` 相关脚本（如 `labelme2yolo.py`、`collect_labelme_class_folders_to_flat.py`、`prepare_classify_dataset.py` 等），与 `td-prepare-dataset`、文档 `labelme_yolo/7542e转YOLOv8-使用说明.md` 的用法保持一致。
- **`dataset/`**：本机存放下载/解压后的数据（**大文件默认不提交 Git**），说明与数据链接见 [`dataset/README.md`](dataset/README.md)。

## 仓库布局（根目录模块）

| 目录 | 说明 |
|------|------|
| `tongue_diag/` | 可安装主包：ROI、分类、数据集准备、SAM 整图→分类流水线等。 |
| `tongue_sam/` | TongueSAM 推理/训练与 `segment_anything` 等，权重放在 `tongue_sam/pretrained_model/`。 |
| `labelme_yolo/` | LabelMe 与 YOLO 格式转换、辅助脚本（如整库说明 `7542e转YOLOv8-使用说明.md`）。 |
| `dataset/` | 本地数据根目录，约定与资源链接见 `dataset/README.md`。 |

## 主包子模块（`tongue_diag`）

| 模块 | 说明 |
|------|------|
| `tongue_diag.roi` | 读取 ROI JSON，扩边、resize、letterbox、CLAHE 等，批量裁切。 |
| `tongue_diag.classify` | Ultralytics YOLO **classify** 的 `train` / `predict`。 |
| `tongue_diag.dataset` | 准备 `train/类名/*`、`val/类名/*`；支持「每类一文件夹」或从 **YOLO 检测** 转换。 |
| `tongue_diag.pipelines` | 端到端脚本，如 **`sam_class_folders`**。 |

## 命令行入口

| 命令 | 作用 |
|------|------|
| `td-roi` | ROI 批处理（同原 `tongue_roi_preprocess` 逻辑） |
| `td-train-cls` | 分类训练 |
| `td-predict-cls` | 分类推理（`--topk`） |
| `td-prepare-dataset` | 子命令 `from-7542e` \| `from-yolo-detect` |
| `td-collect-labelme` | 将多目录 LabelMe json 展平到单目录 |
| `td-prep-sam-cls` | **无检测标注**：类文件夹整图 → TongueSAM → 裁舌 → `train/val`（默认 `--tonguesam-root` 为仓库内 `tongue_sam/`） |

## 无 LabelMe、无检测框：整图 + SAM 裁舌 → 分类数据

1. 准备数据：根目录下 **每个类别一个子文件夹**，内含原始拍摄整图（jpg/png）。
2. 在 **`tongue_sam/pretrained_model/`** 放置 `tonguesam.pth` 等权重（见 `tongue_sam/README.md`）。
3. 执行（示例，PowerShell；已省略 `--tonguesam-root` 时使用本仓库的 `tongue_sam`）：

```text
td-prep-sam-cls ^
  --src D:\data\raw_by_class ^
  --out D:\data\yolo_cls_from_sam ^
  --clean-sam-io ^
  --val-ratio 0.2 ^
  --margin 0 --size 224 --letterbox
```

若需指向其它 TongueSAM 副本，可显式传入 `--tonguesam-root <路径>`。

- `--clean-sam-io`：清空前一次 TongueSAM 的 `data/test_in`、`test_roi`、`test_out`，避免混图。
- 中间件默认写在 `{--out 同级目录下 *_work}`，可用 `--work-dir` 修改。
- 成功后在 `--out` 下得到 `train/类名/*`、`val/类名/*`，可直接 `td-train-cls --data D:\data\yolo_cls_from_sam ...`。
- `td-prep-sam-cls` 通过子进程在 **`tongue_sam` 根目录** 下执行 `python predict.py`；请保证该环境已安装 TongueSAM 侧依赖（通常与根目录 `.venv` 一致）。

## 与历史 `tongue-projects` 的对应关系

- `tongue-roi-preprocess` → `tongue_diag.roi`
- `tongue-yolov8-cls` → `tongue_diag.classify`
- `rooneysh-Labelme2YOLO-main/prepare_classify_dataset.py` → `tongue_diag.dataset`
- 展平 json 脚本 → `tongue_diag.dataset.collect_labelme_flat`
- TongueSAM 上游工程 → 本仓库 `tongue_sam/`
- 原 `rooneysh-Labelme2YOLO-main` → 本仓库 `labelme_yolo/`

在 `labelme_yolo` 下可按原 `7542e转YOLOv8-使用说明.md` 使用 `labelme2yolo.py`；检测格式数据集仍可供 `td-prepare-dataset from-yolo-detect` 使用。

## 许可

以仓库根 `LICENSE` 为准；使用 Ultralytics、TongueSAM 等请遵守其各自许可证。
