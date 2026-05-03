# from PIL import ImageDraw
from __future__ import annotations

import json
import os
import threading
import warnings
from typing import Any

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image, ImageDraw
from segment.yolox import YOLOX
from segment_anything import sam_model_registry
from segment_anything.utils.transforms import ResizeLongestSide
from skimage import io, transform

from utils_metrics import *

join = os.path.join

# 永久性地忽略指定类型的警告
warnings.filterwarnings("ignore", category=UserWarning)
#########################################################################################################
ts_img_path = "./data/test_in/"
model_type = "vit_b"
checkpoint = "./pretrained_model/tonguesam.pth"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
path_out = "./data/test_out/"
path_roi_json = "./data/test_roi/"  # 每图舌区域框（原图像素坐标 xyxy）JSON
os.makedirs(path_roi_json, exist_ok=True)

_sam_model: Any | None = None
_segment: Any | None = None
_model_lock = threading.Lock()

# set seeds
torch.manual_seed(2023)
np.random.seed(2023)


def _ensure_models() -> tuple[Any, Any]:
    """惰性加载 SAM 与 YOLOX，避免 import 本模块即占用大块显存/内存。"""
    global _sam_model, _segment
    with _model_lock:
        if _segment is None:
            _segment = YOLOX(cuda=torch.cuda.is_available())
        if _sam_model is None:
            _sam_model = sam_model_registry[model_type](checkpoint=checkpoint).to(device)
            _sam_model.eval()
        return _sam_model, _segment


##############################################################################################################
def get_bbox_from_mask(mask):
    """Returns a bounding box from a mask"""
    y_indices, x_indices = np.where(mask > 0)
    x_min, x_max = np.min(x_indices), np.max(x_indices)
    y_min, y_max = np.min(y_indices), np.max(y_indices)
    # add perturbation to bounding box coordinates
    H, W = mask.shape
    x_min = max(0, x_min - np.random.randint(0, 20))
    x_max = min(W, x_max + np.random.randint(0, 20))
    y_min = max(0, y_min - np.random.randint(0, 20))
    y_max = min(H, y_max + np.random.randint(0, 20))

    return np.array([x_min, y_min, x_max, y_max], dtype=np.float64)


def bbox_xyxy_from_mask_deterministic(mask: np.ndarray):
    """从二值 mask 取紧外接框，无随机扩边，用于导出 ROI JSON。"""
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    x_min, x_max = int(xs.min()), int(xs.max())
    y_min, y_max = int(ys.min()), int(ys.max())
    return [x_min, y_min, x_max, y_max]


def scale_xyxy_from_infer_to_orig(box_xyxy, orig_wh, infer_wh=(400, 400)):
    """将 infer 画布上的 xyxy 映射回原图。infer 为方形 resize 到 infer_wh。"""
    ow, oh = orig_wh
    iw, ih = infer_wh
    sx = ow / float(iw)
    sy = oh / float(ih)
    x0, y0, x1, y1 = box_xyxy
    x0 = max(0.0, min(float(x0 * sx), float(ow - 1)))
    y0 = max(0.0, min(float(y0 * sy), float(oh - 1)))
    x1 = max(0.0, min(float(x1 * sx), float(ow - 1)))
    y1 = max(0.0, min(float(y1 * sy), float(oh - 1)))
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    return [x0, y0, x1, y1]


def show_mask(mask, ax, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([251 / 255, 252 / 255, 30 / 255, 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)


def show_box(box, ax):
    x0, y0 = box[0], box[1]
    w, h = box[2] - box[0], box[3] - box[1]
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor="blue", facecolor=(0, 0, 0, 0), lw=2))


def run_inference_on_file(f: str, *, write_visual: bool = True) -> None:
    """对 ``ts_img_path`` 下单张图跑 TongueSAM，写出 ROI JSON；可选写出可视化 PNG。"""
    sam_model, segment = _ensure_models()
    with torch.no_grad():
        image_data = io.imread(join(ts_img_path, f))
        orig_h, orig_w = int(image_data.shape[0]), int(image_data.shape[1])

        if image_data.shape[-1] > 3 and len(image_data.shape) == 3:
            image_data = image_data[:, :, :3]
        if len(image_data.shape) == 2:
            image_data = np.repeat(image_data[:, :, None], 3, axis=-1)

        lower_bound, upper_bound = np.percentile(image_data, 0.5), np.percentile(image_data, 99.5)
        image_data_pre = np.clip(image_data, lower_bound, upper_bound)
        image_data_pre = (image_data_pre - np.min(image_data_pre)) / (
            np.max(image_data_pre) - np.min(image_data_pre)
        ) * 255.0
        image_data_pre[image_data == 0] = 0
        image_data_pre = transform.resize(
            image_data_pre, (400, 400), order=3, preserve_range=True, mode="constant", anti_aliasing=True
        )
        image_data_pre = np.uint8(image_data_pre)

        sam_transform = ResizeLongestSide(sam_model.image_encoder.img_size)
        resize_img = sam_transform.apply_image(image_data_pre)
        resize_img_tensor = torch.as_tensor(resize_img.transpose(2, 0, 1)).to(device)
        input_image = sam_model.preprocess(resize_img_tensor[None, :, :, :])
        ts_img_embedding = sam_model.image_encoder(input_image)

        img = image_data_pre
        boxes = segment.get_prompt(img)

        if boxes is not None:
            sam_trans = ResizeLongestSide(sam_model.image_encoder.img_size)
            box = sam_trans.apply_boxes(boxes, (400, 400))
            box_torch = torch.as_tensor(box, dtype=torch.float, device=device)
        else:
            box_torch = None
        sparse_embeddings, dense_embeddings = sam_model.prompt_encoder(
            points=None,
            boxes=box_torch,
            masks=None,
        )

        medsam_seg_prob, _ = sam_model.mask_decoder(
            image_embeddings=ts_img_embedding.to(device),
            image_pe=sam_model.prompt_encoder.get_dense_pe(),
            sparse_prompt_embeddings=sparse_embeddings,
            dense_prompt_embeddings=dense_embeddings,
            multimask_output=False,
        )
        medsam_seg_prob = medsam_seg_prob.cpu().detach().numpy().squeeze()
        medsam_seg = (medsam_seg_prob > 0.5).astype(np.uint8)

        medsam_seg = cv2.resize(medsam_seg, (400, 400))

        box_yolox_orig = box_mask_orig = None
        if boxes is not None:
            b = boxes.astype(np.float64)
            box_yolox_orig = scale_xyxy_from_infer_to_orig([b[0], b[1], b[2], b[3]], (orig_w, orig_h), (400, 400))
        mb = bbox_xyxy_from_mask_deterministic(medsam_seg)
        if mb is not None:
            box_mask_orig = scale_xyxy_from_infer_to_orig(mb, (orig_w, orig_h), (400, 400))

        roi_record = {
            "image_file": f,
            "original_size": {"width": orig_w, "height": orig_h},
            "infer_size": [400, 400],
            "format": "xyxy",
            "space": "original_image_pixels",
            "box_yolox_xyxy": box_yolox_orig,
            "box_mask_xyxy": box_mask_orig,
            "has_yolox_prompt": boxes is not None,
        }
        stem = os.path.splitext(f)[0]
        with open(join(path_roi_json, stem + ".json"), "w", encoding="utf-8") as jf:
            json.dump(roi_record, jf, ensure_ascii=False, indent=2)

        if not write_visual:
            print(f)
            return

        pred = cv2.Canny(cv2.resize((medsam_seg != 0).astype(np.uint8) * 255, (400, 400)), 100, 200)

        for i in range(pred.shape[0]):
            for j in range(pred.shape[1]):
                if pred[i, j] != 0:
                    img[max(i - 1, 0) : min(i + 2, 400), max(j - 1, 0) : min(j + 2, 400), :] = [0, 0, 255]

        image1 = Image.fromarray(medsam_seg)
        image2 = Image.fromarray(img)

        image1 = image1.resize(image2.size).convert("RGBA")
        image2 = image2.convert("RGBA")
        data1 = image1.getdata()

        new_image = Image.new("RGBA", image2.size)
        new_data = [(0, 0, 128, 96) if pixel1[0] != 0 else (0, 0, 0, 0) for pixel1 in data1]

        new_image.putdata(new_data)
        if boxes is not None:
            draw = ImageDraw.Draw(image2)
            draw.rectangle([boxes[0], boxes[1], boxes[2], boxes[3]], fill=None, outline=(0, 255, 0), width=5)
        image2.paste(new_image, (0, 0), mask=new_image)
        image2.save(path_out + f.split(".")[0] + ".png")
        print(f)


def _env_truthy(key: str, default: str = "1") -> bool:
    return os.environ.get(key, default).strip().lower() in ("1", "true", "yes", "on")


def main_batch() -> None:
    """CLI：处理 ``ts_img_path`` 下所有文件（与原脚本行为一致）。"""
    os.makedirs(path_out, exist_ok=True)
    write_visual = _env_truthy("TONGUESAM_WRITE_VISUAL", "1")
    for f in os.listdir(ts_img_path):
        run_inference_on_file(f, write_visual=write_visual)


if __name__ == "__main__":
    main_batch()
