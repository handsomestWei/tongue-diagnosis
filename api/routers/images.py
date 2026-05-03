"""图片与标注 MVP API（P1）。"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth_core import require_roles
from api.config import Settings, get_settings
from api.deps import get_db
from core.derived_regenerate import regenerate_derived_for_image
from db.models import Image, ImageKind, Label, Project
from db.repository import ImageRepository

router = APIRouter(prefix="/api/v1/images", tags=["images"])


def _validate_image_kind(value: str) -> str:
    allowed = [e.value for e in ImageKind]
    if value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效 image_kind，允许: {allowed}",
        )
    return value


def _default_project_id(db: Session) -> int:
    p = db.scalar(select(Project).where(Project.name == "default"))
    if not p:
        raise HTTPException(status_code=500, detail="默认项目缺失，请检查数据库种子")
    return p.id


def _safe_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^a-zA-Z0-9._\-]", "_", base)
    return base[:200] if base else "file"


class ImageOut(BaseModel):
    id: int
    project_id: int
    original_filename: str
    storage_path: str
    image_kind: str
    derived_tongue_path: Optional[str] = None
    preprocess_version: str
    sha256: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class LabelOut(BaseModel):
    id: int
    class_name: str
    source: str


class ImageDetailOut(BaseModel):
    id: int
    project_id: int
    original_filename: str
    storage_path: str
    image_kind: str
    derived_tongue_path: Optional[str] = None
    preprocess_version: str
    sha256: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    labels: list[LabelOut] = []


class ImagePatchBody(BaseModel):
    image_kind: Optional[str] = None
    preprocess_version: Optional[str] = None
    regenerate_derived: bool = Field(
        default=False,
        description="为 True 时按当前 image_kind 立即重算规范舌图并更新 derived_tongue_path（full_face 会调 TongueSAM）",
    )


class LabelPatchBody(BaseModel):
    class_name: str = Field(..., min_length=1, max_length=128)


@router.get("", response_model=list[ImageOut])
def list_images(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
    skip: int = 0,
    limit: int = 100,
):
    rows = db.scalars(select(Image).order_by(Image.id.desc()).offset(skip).limit(limit)).all()
    return [
        ImageOut(
            id=r.id,
            project_id=r.project_id,
            original_filename=r.original_filename,
            storage_path=r.storage_path,
            image_kind=r.image_kind,
            derived_tongue_path=r.derived_tongue_path,
            preprocess_version=r.preprocess_version,
            sha256=r.sha256,
            width=r.width,
            height=r.height,
        )
        for r in rows
    ]


@router.get("/{image_id}", response_model=ImageDetailOut)
def get_image(
    image_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
):
    row = db.get(Image, image_id)
    if not row:
        raise HTTPException(status_code=404, detail="图片不存在")
    labels = [
        LabelOut(id=l.id, class_name=l.class_name, source=l.source)
        for l in sorted(row.labels, key=lambda x: x.id)
    ]
    return ImageDetailOut(
        id=row.id,
        project_id=row.project_id,
        original_filename=row.original_filename,
        storage_path=row.storage_path,
        image_kind=row.image_kind,
        derived_tongue_path=row.derived_tongue_path,
        preprocess_version=row.preprocess_version,
        sha256=row.sha256,
        width=row.width,
        height=row.height,
        labels=labels,
    )


@router.get("/{image_id}/file")
def get_image_file(
    image_id: int,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator", "viewer"))],
    rel: Optional[str] = None,
):
    """返回原始或 derived 图片文件；rel 为 storage_root 下相对路径，默认原图。"""
    row = db.get(Image, image_id)
    if not row:
        raise HTTPException(status_code=404, detail="图片不存在")
    root = Path(settings.storage_root).resolve()
    sub = (rel or row.storage_path or "").replace("\\", "/").lstrip("/")
    if ".." in Path(sub).parts:
        raise HTTPException(status_code=400, detail="非法路径")
    path = (root / sub).resolve()
    try:
        ok = path.is_relative_to(root)
    except AttributeError:
        ok = str(path).startswith(str(root) + os.sep) or path == root
    if not ok:
        raise HTTPException(status_code=400, detail="路径须位于 storage_root 下")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(path), filename=path.name)


@router.post("/upload", response_model=ImageOut)
async def upload_image(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[dict, Depends(require_roles("admin", "annotator"))],
    settings: Annotated[Settings, Depends(get_settings)],
    file: UploadFile = File(...),
    image_kind: str = Form(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")
    kind = _validate_image_kind(image_kind)

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")

    digest = hashlib.sha256(raw).hexdigest()
    pid = _default_project_id(db)

    base = Path(settings.storage_root).resolve() / "projects" / str(pid) / "images"
    base.mkdir(parents=True, exist_ok=True)
    ext = Path(_safe_filename(file.filename)).suffix or ".bin"
    sub = f"{digest[:16]}{ext}"
    abs_path = base / sub
    rel_path = os.path.relpath(abs_path, Path(settings.storage_root).resolve())
    if not abs_path.is_file():
        abs_path.write_bytes(raw)

    # 简易尺寸（需 pillow 可选；无则留空）
    w = h = None
    try:
        from PIL import Image as PilImage

        import io

        im = PilImage.open(io.BytesIO(raw))
        w, h = im.size
    except Exception:
        pass

    row = Image(
        project_id=pid,
        uploaded_by_id=user.get("id"),
        storage_path=rel_path.replace("\\", "/"),
        original_filename=file.filename,
        sha256=digest,
        image_kind=kind,
        preprocess_version="v1",
        width=w,
        height=h,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ImageOut(
        id=row.id,
        project_id=row.project_id,
        original_filename=row.original_filename,
        storage_path=row.storage_path,
        image_kind=row.image_kind,
        derived_tongue_path=row.derived_tongue_path,
        preprocess_version=row.preprocess_version,
        sha256=row.sha256,
        width=row.width,
        height=row.height,
    )


@router.patch("/{image_id}", response_model=ImageOut)
def patch_image(
    image_id: int,
    body: ImagePatchBody,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator"))],
):
    row = db.get(Image, image_id)
    if not row:
        raise HTTPException(status_code=404, detail="图片不存在")
    if body.image_kind is not None:
        row.image_kind = _validate_image_kind(body.image_kind)
    if body.preprocess_version is not None:
        row.preprocess_version = body.preprocess_version
    if body.regenerate_derived:
        try:
            regenerate_derived_for_image(db, settings, row)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except RuntimeError as e:
            raise HTTPException(status_code=502, detail=str(e)) from e
    db.add(row)
    db.commit()
    db.refresh(row)
    return ImageOut(
        id=row.id,
        project_id=row.project_id,
        original_filename=row.original_filename,
        storage_path=row.storage_path,
        image_kind=row.image_kind,
        derived_tongue_path=row.derived_tongue_path,
        preprocess_version=row.preprocess_version,
        sha256=row.sha256,
        width=row.width,
        height=row.height,
    )


@router.patch("/{image_id}/labels", response_model=dict)
def patch_labels(
    image_id: int,
    body: LabelPatchBody,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[dict, Depends(require_roles("admin", "annotator"))],
):
    repo = ImageRepository(db, settings)
    row = repo.get(image_id)
    if not row:
        raise HTTPException(status_code=404, detail="图片不存在")
    repo.replace_manual_label(image_id, body.class_name)
    return {"ok": True, "image_id": image_id, "class_name": body.class_name}
