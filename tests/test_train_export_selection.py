import json

import cv2
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.config import Settings
from core.train_export import export_yolo_classify_from_db
from db.base import Base
from db.models import Correction, Image, Label, ModelRegistry, Prediction, Project


def _make_db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def test_export_corrections_only_uses_flagged_class(tmp_path):
    db = _make_db()
    p = Project(name="p1")
    db.add(p)
    db.commit()
    db.refresh(p)

    img = Image(
        project_id=p.id,
        storage_path="raw/1.png",
        original_filename="1.png",
        image_kind="tongue_closeup",
    )
    db.add(img)
    db.commit()
    db.refresh(img)

    db.add(Label(image_id=img.id, class_name="淡红舌", source="manual"))
    m = ModelRegistry(name="demo", path="/tmp/x.pt", is_default=False)
    db.add(m)
    db.commit()
    db.refresh(m)

    pred = Prediction(image_id=img.id, model_id=m.id, result_json=json.dumps({"topk": [{"class": "红舌", "score": 0.9}]}))
    db.add(pred)
    db.commit()
    db.refresh(pred)

    db.add(
        Correction(
            prediction_id=pred.id,
            correct_class="紫舌",
            include_in_next_train=True,
        )
    )
    db.commit()

    root = tmp_path / "ds"
    storage = tmp_path / "st"
    (storage / "raw").mkdir(parents=True)
    cv2.imwrite(str(storage / "raw" / "1.png"), np.zeros((32, 32, 3), dtype=np.uint8))

    s = Settings(
        database_url="sqlite://",
        storage_root=str(storage),
        tonguesam_root=str(tmp_path / "sam"),
        classify_weights_path="",
        infer_imgsz=32,
    )
    _out, stats, summary = export_yolo_classify_from_db(
        db, s, out_root=root, val_ratio=0.0, imgsz=32, selection="corrections_flagged", merge_base_manual=False
    )
    assert stats.total_exported >= 1
    assert any(x["class"] == "紫舌" for x in summary["images"])


def test_export_merge_overrides_manual_class(tmp_path):
    db = _make_db()
    p = Project(name="p1")
    db.add(p)
    db.commit()
    db.refresh(p)

    img = Image(
        project_id=p.id,
        storage_path="raw/1.png",
        original_filename="1.png",
        image_kind="tongue_closeup",
    )
    db.add(img)
    db.commit()
    db.refresh(img)

    db.add(Label(image_id=img.id, class_name="淡红舌", source="manual"))
    m = ModelRegistry(name="demo", path="/tmp/x.pt", is_default=False)
    db.add(m)
    db.commit()
    db.refresh(m)

    pred = Prediction(image_id=img.id, model_id=m.id, result_json="{}")
    db.add(pred)
    db.commit()
    db.refresh(pred)

    db.add(Correction(prediction_id=pred.id, correct_class="override类", include_in_next_train=True))
    db.commit()

    root = tmp_path / "ds"
    storage = tmp_path / "st"
    (storage / "raw").mkdir(parents=True)
    cv2.imwrite(str(storage / "raw" / "1.png"), np.zeros((32, 32, 3), dtype=np.uint8))

    s = Settings(
        database_url="sqlite://",
        storage_root=str(storage),
        tonguesam_root=str(tmp_path / "sam"),
        classify_weights_path="",
        infer_imgsz=32,
    )
    _out, _stats, summary = export_yolo_classify_from_db(
        db, s, out_root=root, val_ratio=0.0, imgsz=32, selection="corrections_flagged", merge_base_manual=True
    )
    assert any(x["class"] == "override类" for x in summary["images"])
