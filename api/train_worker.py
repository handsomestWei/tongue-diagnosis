"""后台执行 TrainJob：导出数据集 + Ultralytics classify 训练。"""
from __future__ import annotations

import json
import logging
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from api.config import Settings, get_settings
from core.train_export import export_yolo_classify_from_db
from db.models import ModelRegistry, TrainJob, TrainJobStatus
from db.session import get_session_factory

log = logging.getLogger(__name__)


def _find_best_pt(search_root: Path) -> Path | None:
    cands = sorted(search_root.rglob("best.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def _run_train_job_impl(job_id: str, settings: Settings) -> None:
    SessionLocal = get_session_factory()
    with SessionLocal() as db:
        job = db.get(TrainJob, job_id)
        if not job:
            log.error("TrainJob missing: %s", job_id)
            return
        params = json.loads(job.params_json or "{}")
        job.status = TrainJobStatus.running.value
        job.started_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()

    work = Path(settings.train_work_root).resolve() / job_id
    dataset_dir = work / "dataset"
    ultra_project = work / "ultra_runs"
    log_path = work / "train.log"

    def log_line(msg: str) -> None:
        work.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} {msg}\n")

    try:
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True, exist_ok=True)
        log_line("开始导出训练数据")

        with SessionLocal() as db:
            export_yolo_classify_from_db(
                db,
                settings,
                out_root=dataset_dir,
                val_ratio=float(params.get("val_ratio", 0.2)),
                seed=int(params.get("seed", 42)),
                margin=float(params.get("margin", 0.12)),
                letterbox=bool(params.get("letterbox", True)),
                clahe=bool(params.get("clahe", True)),
                unsharp=bool(params.get("unsharp", False)),
                update_derived_paths=True,
                imgsz=int(params.get("imgsz", settings.infer_imgsz)),
                selection=str(params.get("export_selection", "all_manual")),
                merge_base_manual=bool(params.get("merge_base_manual", False)),
            )

        log_line("导出完成，开始 YOLO 训练")
        from ultralytics import YOLO

        if params.get("job_subtype") == "incremental":
            model_name = str(params.get("parent_weights") or params.get("model", "yolov8n-cls.pt"))
        else:
            model_name = params.get("model", "yolov8n-cls.pt")
        model = YOLO(model_name)
        train_kw: dict = dict(
            data=str(dataset_dir.resolve()),
            epochs=int(params.get("epochs", 1)),
            imgsz=int(params.get("imgsz", settings.infer_imgsz)),
            batch=int(params.get("batch", 4)),
            project=str(ultra_project),
            name="cls",
            exist_ok=True,
            verbose=False,
        )
        if settings.train_device:
            train_kw["device"] = settings.train_device

        results = model.train(**train_kw)
        save_dir = Path(getattr(results, "save_dir", ultra_project / "cls"))
        best = save_dir / "weights" / "best.pt"
        if not best.is_file():
            alt = _find_best_pt(ultra_project)
            best = alt if alt else best

        if not best.is_file():
            raise FileNotFoundError(f"未找到 best.pt，请检查 Ultralytics 输出目录: {ultra_project}")

        metrics: dict | None = None
        try:
            if results and hasattr(results, "results_dict"):
                metrics = dict(results.results_dict)
        except Exception:
            pass

        with SessionLocal() as db:
            job = db.get(TrainJob, job_id)
            if not job:
                return
            reg = ModelRegistry(
                name=params.get("register_name", f"train-{job_id[:8]}"),
                path=str(best.resolve()),
                metrics_json=json.dumps(metrics, ensure_ascii=False) if metrics else None,
                is_default=bool(params.get("set_as_default")),
                status="registered",
            )
            if reg.is_default:
                for m in db.scalars(select(ModelRegistry).where(ModelRegistry.is_default.is_(True))).all():
                    m.is_default = False
                    db.add(m)
            db.add(reg)
            job.status = TrainJobStatus.success.value
            job.log_path = str(log_path)
            job.metrics_json = json.dumps(metrics, ensure_ascii=False) if metrics else None
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
        log_line(f"训练成功 best={best}")
    except Exception as e:
        log.exception("Train job %s failed", job_id)
        log_line(f"失败: {e}")
        with SessionLocal() as db:
            job = db.get(TrainJob, job_id)
            if job:
                job.status = TrainJobStatus.failed.value
                job.error_message = str(e)
                job.log_path = str(log_path) if work.exists() else job.log_path
                job.finished_at = datetime.now(timezone.utc)
                db.add(job)
                db.commit()


def run_train_job_background(job_id: str) -> None:
    settings = get_settings()
    _run_train_job_impl(job_id, settings)


def spawn_train_job_thread(job_id: str) -> None:
    t = threading.Thread(target=run_train_job_background, args=(job_id,), daemon=True)
    t.start()
