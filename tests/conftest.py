"""测试启动前固定环境变量（须在 import api 之前由 pytest 加载）。"""
from __future__ import annotations

import os
from pathlib import Path

_db = Path("/tmp/td_pytest.db")
if _db.is_file():
    _db.unlink()

os.environ["DATABASE_URL"] = "sqlite:////tmp/td_pytest.db"
os.environ["STORAGE_ROOT"] = "/tmp/td_pytest_storage"
os.environ["SEED_DEMO_USERS"] = "true"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["CLASSIFY_WEIGHTS_PATH"] = ""

Path(os.environ["STORAGE_ROOT"]).mkdir(parents=True, exist_ok=True)
