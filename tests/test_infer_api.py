import cv2
import numpy as np
import pytest
from starlette.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client: TestClient):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_infer_upload_demo(client: TestClient, admin_token: str):
    img = np.zeros((16, 16, 3), dtype=np.uint8)
    img[:, :] = (40, 50, 60)
    _, buf = cv2.imencode(".png", img)
    png = buf.tobytes()
    files = {"file": ("x.png", png, "image/png")}
    r = client.post(
        "/api/v1/infer",
        files=files,
        data={"image_kind": "tongue_closeup", "topk": 2},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["demo"] is True
    assert len(body["topk"]) == 2
    assert body["sam_called"] is False


def test_infer_requires_kind_or_id(client: TestClient, admin_token: str):
    r = client.post(
        "/api/v1/infer",
        files={"file": ("x.png", b"x", "image/png")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 400
