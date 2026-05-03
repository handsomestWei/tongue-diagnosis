"""测试启动前固定环境变量（须在 import api 之前由 pytest 加载）。"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
else:
    _db = Path("/tmp/td_pytest.db")
    if _db.is_file():
        _db.unlink()
    os.environ["DATABASE_URL"] = "sqlite:////tmp/td_pytest.db"

os.environ["STORAGE_ROOT"] = os.environ.get("STORAGE_ROOT", "/tmp/td_pytest_storage")
os.environ["SEED_DEMO_USERS"] = "true"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["CLASSIFY_WEIGHTS_PATH"] = ""
os.environ["RATE_LIMIT_PER_MINUTE"] = os.environ.get("RATE_LIMIT_PER_MINUTE", "0")

Path(os.environ["STORAGE_ROOT"]).mkdir(parents=True, exist_ok=True)

from api.config import get_settings  # noqa: E402
import api.rate_limit as _rate_limit  # noqa: E402

get_settings.cache_clear()
_rate_limit._windows.clear()


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    import api.rate_limit as rl

    rl._windows.clear()
    yield
    rl._windows.clear()
