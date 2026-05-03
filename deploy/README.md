# 部署说明

生产建议使用：

- **API**：`uvicorn api.main:app --host 0.0.0.0 --port 8000`，`PYTHONPATH` 指向仓库根，或 `pip install -e ".[api]"`
- **前端**：`web/` 下 `npm ci && npm run build`，由 Nginx 托管 `dist/`，或将 `dist` 挂载到 FastAPI `StaticFiles`（可按需自行扩展 `api/main.py`）
- **环境**：复制 `.env.example` → `.env`，生产关闭 `AUTO_CREATE_TABLES` / `SEED_DEMO_USERS`，使用 `alembic upgrade head` 与真实用户

## Docker（草图）

在**仓库根**执行：

```bash
docker build -f deploy/Dockerfile -t tongue-api:local .
docker compose -f deploy/docker-compose.yml up
```

镜像默认仅含服务化 API 依赖；**全脸 + TongueSAM** 需在镜像中安装 `tongue_sam` 侧库与权重，或宿主机挂载 `TONGUESAM_ROOT`。
