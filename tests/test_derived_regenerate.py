import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.config import Settings
from core.derived_regenerate import regenerate_derived_for_image
from db.base import Base
from db.models import Image, Project


def test_regenerate_derived_closeup(tmp_path):
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    db = Session()

    st = tmp_path / "storage"
    (st / "projects" / "1" / "images").mkdir(parents=True)
    raw_rel = "projects/1/images/test.png"
    raw_abs = st / raw_rel
    import cv2

    cv2.imwrite(str(raw_abs), np.zeros((40, 40, 3), dtype=np.uint8))

    p = Project(name="p1")
    db.add(p)
    db.commit()
    db.refresh(p)

    img = Image(
        project_id=p.id,
        storage_path=raw_rel,
        original_filename="x.png",
        image_kind="tongue_closeup",
        sha256="a" * 64,
    )
    db.add(img)
    db.commit()
    db.refresh(img)

    s = Settings(
        storage_root=str(st),
        tonguesam_root=str(tmp_path / "sam"),
        infer_imgsz=32,
        infer_sam_timeout_sec=60,
    )
    rel = regenerate_derived_for_image(db, s, img)
    assert "derived" in rel
    assert (st / rel).is_file()
    db.refresh(img)
    assert img.derived_tongue_path == rel
