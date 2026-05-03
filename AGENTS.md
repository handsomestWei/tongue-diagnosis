# 代理说明（Agents）

面向在 Cursor Cloud 或其它自动化环境中开发本仓库的说明。

## Cursor Cloud specific instructions

- **Python 路径**：建议在仓库根目录使用 **Python 3.10** 虚拟环境 `.venv`，并安装 `pip install -e ".[api,dev]"`（API 与测试：`sqlalchemy`、`alembic`、`fastapi` 等在 `api` extra 中）。若未通过可编辑安装，运行 `uvicorn` / `pytest` 时需设置 **`PYTHONPATH` 指向仓库根**，否则 `import api`、`import db` 会失败。
- **环境变量（后端）**：`DATABASE_URL`（默认 `sqlite:///./data/app.db`）、`STORAGE_ROOT`（默认 `./storage`）、`JWT_SECRET_KEY` 等由 `api/config.py`（pydantic-settings）读取。开发默认 **`AUTO_CREATE_TABLES=true`** 与 **`SEED_DEMO_USERS=true`** 会在启动时 `create_all` 并种子 `admin` / `annotator` / `viewer`（口令见配置项 `dev_*_password`）；**生产应关闭**上述两项，仅使用 **Alembic** 与真实用户数据源。
- **数据库迁移**：根目录已有 `alembic.ini` 与 `migrations/`。在仓库根执行：`PYTHONPATH=. alembic upgrade head`（需已安装 `api` 依赖）。SQLite 路径的父目录会在迁移与应用启动时尽量自动创建。
- **上传接口路径**：图片上传为 **`POST /api/v1/images/upload`**（multipart：`file` + 必选表单字段 **`image_kind`** ∈ `full_face_selfie` | `tongue_closeup`）。标注为 **`PATCH /api/v1/images/{id}/labels`**。**viewer 角色**对该类写操作会 **403**（由后端强制）。
- **推理**：`POST /api/v1/infer` — **上传**时须带 `image_kind` + `file`；**仅** `image_id` 时从库读取类型与文件。环境变量 **`CLASSIFY_WEIGHTS_PATH`** 指向 `.pt` 且存在则跑 **Ultralytics YOLO classify**（CPU 见 `INFER_DEVICE`）；未配置则返回演示 top-k。`full_face_selfie` 会通过子进程执行 **`TONGUESAM_ROOT`/predict.py**（超时 `INFER_SAM_TIMEOUT_SEC`）；特写 **不调 SAM**。核心逻辑在 `core/`。
- **批量推理**：**`POST /api/v1/infer/batch`**（JSON：`image_ids`、`topk`）。当前在**请求进程内同步**顺序执行，结果写入 **`async_jobs`**。**`GET /api/v1/jobs/{job_id}`** 返回 `payload` / `result`（`items` 每图结果，`errors` 失败汇总）。生产可改为后台 Worker。
- **训练（P3）**：`POST /api/v1/train` 启动**后台线程**：导出带 **manual** 标注的 YOLO classify 数据 → `ultralytics` 训练 → 写 **`model_registry`**（`TRAIN_WORK_ROOT`、`TRAIN_DEVICE`）。无标注会失败。种子含占位模型 **`demo-no-weights`**；真实权重训练后请用 **`/models` 返回的 id** 作为 `infer` 的 `model_id`。**`POST /api/v1/train/incremental`**：在可读父 **.pt** 上继续训练（参数见 OpenAPI）。
- **请求 ID**：响应头 **`X-Request-ID`**（可客户端传入同名字段）。
- **预测与纠错**：`GET /api/v1/predictions`、`POST /api/v1/predictions/{id}/correct`（写 `corrections` 并同步人工 `labels`）。`POST /infer` 在 **image_id** 模式下可表单字段 **`persist=true`** 写入 `predictions`。
- **图片文件**：`GET /api/v1/images/{id}/file?rel=` 可选 `derived_tongue_path`，供预览（需 Bearer）。
- **前端**：`web/` 下 `npm ci`（或 `npm install`）后 `npm run dev`；`vite` 将 **`/api` 代理** 到 `http://127.0.0.1:8000`。演示账号与 RBAC 行为见 `web/src/views/LoginView.vue` 提示。
- **测试**：`pytest tests/`（`conftest.py` 固定临时 SQLite；需 `pip install -e ".[api,dev]"` 且 **`PYTHONPATH` 为仓库根**）。

标准安装与 TongueSAM、数据目录约定仍以 **`README.md`** 与 **`docs/`** 设计文档为准；此处仅补充本阶段服务化后**不显眼但易踩坑**的项。
