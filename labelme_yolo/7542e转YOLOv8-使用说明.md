# 类文件夹 LabelMe（例：7542e-main）→ YOLOv8 训练数据：主线操作

目标：把本仓库下 **`dataset/`** 中按 LabelMe 保存的原始标注（**示例**目录名 `7542e-main`：每类一子文件夹、内含 `*.json`），变成 Ultralytics **YOLOv8 检测或分割** 用的 `dataset.yaml` + `images/` + `labels/`。数据下载与参考链接见 [`dataset/README.md`](../dataset/README.md)。

（若目标是 **整图分类**，见下文「和分类是什么关系」——不必死磕这一套目录。）

---

## 主线就四步

在仓库的 **`labelme_yolo/`** 目录下操作（路径按你本机、以下以「仓库根」为 `tongue-diagnosis` 为例，可用相对路径或绝对路径）。

| 步骤 | 做什么 | 命令（示例） |
|:--:|--------|--------------|
| **① 环境** | 装本目录依赖 + ultralytics | `pip install -r requirements.txt` 然后 `pip install ultralytics` |
| **② 扁平化** | `labelme2yolo.py` 只读**单层目录**里的 json，若数据是「每类一子文件夹」必须先汇总 | `python collect_labelme_class_folders_to_flat.py --src ..\dataset\7542e-main --dst ..\dataset\7542e_labelme_flat` |
| **③ 转 YOLO 格式** | 生成 `YOLODataset/` 与 **`dataset.yaml`** | 仅影响 **检测 vs 分割**（见下表），不是「分类 vs 检测」 |
| **④ 开训** | 用生成的 yaml 指向数据 | 与③同列命令 |

### 检测 vs 分割：区别与推荐

| | **检测（detect）** | **分割（segment，`--seg`）** |
|--|-------------------|---------------------------|
| **标签里长什么样** | 把你的多边形压成 **矩形框**（外接框），只学「框在哪」 | 保留 **多边形/掩码**，学「轮廓贴边」 |
| **模型输出** | 框 + 类别 | 框 + **像素级 mask** + 类别 |
| **算力与速度** | 更轻、训练/推理一般更快 | 更重、显存与时间通常更多 |
| **适合什么** | 主要为了 **定位 / 裁剪 ROI**，后面再接分类或其它 | 需要 **边缘、面积、形状** 或与临床标注轮廓强一致 |

**推荐怎么选**

- 你的主线若是 **方案 A：先 ROI 再分类**，且舌在图里已较居中、只要 **稳定框出舌区** → **优先用检测**（`YOLODataset` + `yolo detect train` + `yolov8n.pt`）。  
- 若任务明确要 **舌苔边界、覆盖比例、几何特征**（像素级）→ 用 **分割**（`YOLODataset_seg` + `yolo segment train` + `yolov8n-seg.pt`）。

不确定时：**先检测跑通**，不够再加分割。

### 和「分类」是什么关系？（容易混）

- **这类数据**（类文件夹 + LabelMe）：每张图属于哪一类舌苔，**语义上完全可以做分类**；类别在文件夹名 / json 的 `label` 里都有。  
- **你选的这条「检测」流水线**：产出的是 **目标检测** 数据集——`labels/*.txt` 里是 **`class_id + 框`**。用 Ultralytics 时要走 **`yolo detect train`**，学的是 **框 + 类**，**不是** `yolo classify train` 那种「整图一个类」。  
- **因此**：`YOLODataset` **不是** 分类任务要求的 `train/类名/图片.jpg` 结构；**不是**数据「不能分类」，而是 **这套文件夹格式对接的是检测（或分割），不是 classify 接口**。  
- **若你要训 YOLO 分类**：可直接用**按类分好子文件夹的整图**（如 `7542e-main` 或你自命名目录），**不必**先跑 `labelme2yolo`。也可用本仓脚本一键生成 `train/类名`、`val/类名`：  
  - 从**每类一子文件夹**的源图：`python prepare_classify_dataset.py from-7542e --src ..\dataset\7542e-main --out ..\dataset\tongue_cls_yolov8 --val-ratio 0.2`（子命令名 `from-7542e` 仅表示**目录组织方式**）  
  - 从已有 **YOLODataset**：`python prepare_classify_dataset.py from-yolo-detect --dataset ..\dataset\7542e_labelme_flat\YOLODataset --out ..\dataset\tongue_cls_from_yolo`  
  详见脚本顶部说明 [prepare_classify_dataset.py](prepare_classify_dataset.py)。  

**小结**：上面的 **二选一** = 「标注转成 **检测框** 还是 **分割多边形**」；**不等于**「能不能做分类」。分类是 **另一种数据摆法 + `classify` 命令**。

---

**③ 转格式（按上面选择执行其一）**

- **检测训练**（多边形会变成外接框）：  
  `python labelme2yolo.py --json_dir ..\dataset\7542e_labelme_flat --val_size 0.2`  
  → 输出：`..\dataset\7542e_labelme_flat\YOLODataset\dataset.yaml`

- **分割训练**（保留多边形为 YOLO 分割标签）：  
  `python labelme2yolo.py --json_dir ..\dataset\7542e_labelme_flat --val_size 0.2 --seg`  
  → 输出：`..\dataset\7542e_labelme_flat\YOLODataset_seg\dataset.yaml`

**④ 训练（与上面对应）**

- 检测：  
  `yolo detect train data=完整路径\YOLODataset\dataset.yaml model=yolov8n.pt epochs=100 imgsz=640`

- 分割：  
  `yolo segment train data=完整路径\YOLODataset_seg\dataset.yaml model=yolov8n-seg.pt epochs=100 imgsz=640`

`data=` 建议写 **`dataset.yaml` 的绝对路径**，避免工作目录变化找不到图。

---

## 你需要记住的两点

1. **类别名字**（检测/分割里的 `names`）来自每个 json 里 **`shapes[].label`**，不是扁平化后的文件名。  
2. **整图分类**：优先用**按类分文件夹的整图** 直接接 `td-train-cls`；与本文 **`labelme2yolo` → `YOLODataset`** 是两条线，按需选用。

---

## 附：常见问题

| 问题 | 处理 |
|------|------|
| 训练报找不到图片 | `dataset.yaml` 里 `train`/`val` 改成绝对路径，或 `data=` 用 yaml 绝对路径 |
| 类别数不对 | 统一各 json 里 `label` 字符串拼写 |

脚本来源：[labelme2yolo.py](labelme2yolo.py)（[rooneysh/Labelme2YOLO](https://github.com/rooneysh/Labelme2YOLO)）。第三方数据与工具许可分别以各 LICENSE 与发布方为准。

*文档更新：路径已与 `tongue-diagnosis` 仓库及 `collect_labelme_class_folders_to_flat.py` 命名对齐。*
