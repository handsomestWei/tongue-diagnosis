# Web UI 页面预览截图

本目录由 `web/scripts/capture-ui.mjs` 自动生成：启动 **FastAPI**（`GET /health`、`POST /api/v1/auth/login`）与 **vite preview**，以 **admin** 会话（除登录页外）截取各路由。

| 文件 | 路由 | 说明 |
|------|------|------|
| `00-login.png` | `/login` | 登录页（未注入会话） |
| `01-dashboard.png` | `/` | 仪表盘 |
| `02-upload.png` | `/upload` | 批量上传 |
| `03-annotate.png` | `/annotate` | 标注工作台 |
| `04-train.png` | `/train` | 全量训练 |
| `05-train-incremental.png` | `/train/incremental` | 增量训练 |
| `06-infer.png` | `/infer` | 批量推理 |
| `07-review.png` | `/review` | 纠错审核 |
| `08-models.png` | `/models` | 模型管理（需 admin） |
| `09-settings.png` | `/settings` | 系统设置（需 admin） |

## 重新生成

在仓库根目录确保已 `.venv` 且 `pip install -e ".[api]"`，然后：

```bash
cd web
npm install
npm run capture-ui
```

开发联调：终端 1 `uvicorn api.main:app --reload`（仓库根）；终端 2 `cd web && npm run dev`。演示账号见 `web/README.md`。
