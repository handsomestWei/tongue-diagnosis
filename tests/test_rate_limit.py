import pytest
from starlette.testclient import TestClient


def test_rate_limit_returns_429(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")

    import api.rate_limit as rl
    from api.config import get_settings

    rl._windows.clear()
    get_settings.cache_clear()

    from api.main import app

    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        r2 = client.get("/api/v1/auth/me", headers=h)
        assert r2.status_code == 200
        r3 = client.get("/api/v1/auth/me", headers=h)
        assert r3.status_code == 429
