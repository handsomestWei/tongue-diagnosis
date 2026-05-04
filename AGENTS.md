# 代理说明（Agents）

面向在 Cursor Cloud 或其它自动化环境中开发本仓库的说明。

## Cursor Cloud specific instructions

- **Python 路径**：建议在仓库根目录使用 **Python 3.10** 虚拟环境 `.venv`，并安装 `pip install -e ".[api,dev]"`（API 与测试：`sqlalchemy`、`alembic`、`fastapi` 等在 `api` extra 中）。若未通过可编辑安装，运行 `uvicorn` / `pytest` 时需设置 **`PYTHONPATH` 指向仓库根**，否则 `import api`、`import db` 会失败。
- **环境变量（后端）**：`DATABASE_URL`（默认 `sqlite:///./data/app.db`）、`STORAGE_ROOT`（默认 `./storage`）、`JWT_SECRET_KEY` 等由 `api/config.py`（pydantic-settings）读取。开发默认 **`AUTO_CREATE_TABLES=true`** 与 **`SEED_DEMO_USERS=true`** 会在启动时 `create_all` 并种子 `admin` / `annotator` / `viewer`（口令见配置项 `dev_*_password`）；**生产应关闭**上述两项，仅使用 **Alembic** 与真实用户数据源。
- **数据库迁移**：根目录已有 `alembic.ini` 与 `migrations/`。在仓库根执行：`PYTHONPATH=. alembic upgrade head`（需已安装 `api` 依赖）。SQLite 路径的父目录会在迁移与应用启动时尽量自动创建。
- **上传接口路径**：图片上传为 **`POST /api/v1/images/upload`**（multipart：`file` + 必选表单字段 **`image_kind`** ∈ `full_face_selfie` | `tongue_closeup`）。标注为 **`PATCH /api/v1/images/{id}/labels`**。**viewer 角色**对该类写操作会 **403**（由后端强制）。
- **占位接口**：`POST /api/v1/infer` 为 P2 前的演示占位；`POST /api/v1/train` 仅写入 `train_jobs` 表，尚未执行真实 YOLO 训练。标准跑法仍以根目录 `README.md` 中的 CLI（`td-train-cls` 等）为准。
- **前端**：`web/` 下 `npm ci`（或 `npm install`）后 `npm run dev`；`vite` 将 **`/api` 代理** 到 `http://127.0.0.1:8000`。演示账号与 RBAC 行为见 `web/src/views/LoginView.vue` 提示。
- **测试**：`pytest tests/test_api_mvp.py`（依赖 `pip install -e ".[api,dev]"` 与 **`PYTHONPATH` 为仓库根**，测试内会切换临时 SQLite DB）。

标准安装与 TongueSAM、数据目录约定仍以 **`README.md`** 与 **`docs/`** 设计文档为准；此处仅补充本阶段服务化后**不显眼但易踩坑**的项。
