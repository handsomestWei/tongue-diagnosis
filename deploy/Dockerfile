# CPU-only API 镜像（无 CUDA）。完整 TongueSAM 依赖较重，可按需在镜像中追加 tongue_sam 依赖或挂载宿主机环境。
FROM python:3.10-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md alembic.ini ./
COPY tongue_diag ./tongue_diag
COPY api ./api
COPY core ./core
COPY db ./db
COPY migrations ./migrations

RUN pip install --no-cache-dir pip setuptools wheel \
    && pip install --no-cache-dir -e ".[api]"

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
