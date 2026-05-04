from starlette.testclient import TestClient

from api.main import app


def test_train_list_includes_job_hint():
    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        r2 = client.get("/api/v1/train", headers=h)
        assert r2.status_code == 200
        data = r2.json()
        assert isinstance(data, list)
        if data:
            assert "job_hint" in data[0]
