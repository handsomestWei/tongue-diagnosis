# Web UI 页面预览截图

本目录由 `web/scripts/capture-ui.mjs` 自动生成（Vue 3 + Element Plus 演示界面），便于在设计评审或文档中快速查看各功能页布局。

| 文件 | 路由 | 说明 |
|------|------|------|
| `01-dashboard.png` | `/` | 仪表盘 |
| `02-upload.png` | `/upload` | 批量上传（含 image_kind） |
| `03-annotate.png` | `/annotate` | 标注工作台 |
| `04-train.png` | `/train` | 全量训练 |
| `05-train-incremental.png` | `/train/incremental` | 增量训练 |
| `06-infer.png` | `/infer` | 批量推理 |
| `07-review.png` | `/review` | 纠错审核 |
| `08-models.png` | `/models` | 模型管理 |
| `09-settings.png` | `/settings` | 系统设置 |

## 重新生成

```bash
cd web
npm install
npm run capture-ui
```

或在开发模式下本地预览：`cd web && npm run dev`，默认 <http://localhost:5173>。
