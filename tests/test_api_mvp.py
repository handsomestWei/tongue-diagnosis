import os
from pathlib import Path

import pytest
from starlette.testclient import TestClient

_tmp_db = Path("/tmp/td_test_api.db")
if _tmp_db.is_file():
    _tmp_db.unlink()

os.environ["DATABASE_URL"] = "sqlite:////tmp/td_test_api.db"
os.environ["STORAGE_ROOT"] = "/tmp/td_test_storage"
os.environ["SEED_DEMO_USERS"] = "true"
os.environ["AUTO_CREATE_TABLES"] = "true"

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


def test_login_and_me(client: TestClient, admin_token: str):
    r = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


def test_upload_requires_image_kind(client: TestClient, admin_token: str):
    files = {"file": ("x.png", b"\x89PNG\r\n\x1a\n", "image/png")}
    r = client.post(
        "/api/v1/images/upload",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 422

    r2 = client.post(
        "/api/v1/images/upload",
        files=files,
        data={"image_kind": "invalid"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r2.status_code == 400


def test_upload_and_label(client: TestClient, admin_token: str):
    files = {"file": ("x.png", b"\x89PNG\r\n\x1a\n", "image/png")}
    r = client.post(
        "/api/v1/images/upload",
        files=files,
        data={"image_kind": "tongue_closeup"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text
    img_id = r.json()["id"]
    r3 = client.patch(
        f"/api/v1/images/{img_id}/labels",
        json={"class_name": "淡红舌"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r3.status_code == 200


def test_viewer_cannot_upload(client: TestClient):
    r = client.post(
        "/api/v1/auth/login",
        data={"username": "viewer", "password": "view123"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    files = {"file": ("x.png", b"\x89PNG\r\n\x1a\n", "image/png")}
    r2 = client.post(
        "/api/v1/images/upload",
        files=files,
        data={"image_kind": "tongue_closeup"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 403
