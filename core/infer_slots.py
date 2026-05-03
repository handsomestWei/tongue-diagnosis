"""推理与 TongueSAM 子进程的进程内并发槽（读 os.environ，见 api.main lifespan 同步）。"""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager

_infer_sem: threading.BoundedSemaphore | None = None
_sam_sem: threading.BoundedSemaphore | None = None
_lock = threading.Lock()


def _bounded(cap: int, fallback: int) -> int:
    if cap <= 0:
        return max(1, fallback)
    return max(1, min(cap, 64))


def _infer_cap() -> int:
    raw = os.environ.get("INFER_CONCURRENCY", "4")
    try:
        return int(str(raw).strip())
    except ValueError:
        return 4


def _sam_cap() -> int:
    raw = os.environ.get("INFER_SAM_CONCURRENCY", "1")
    try:
        return int(str(raw).strip())
    except ValueError:
        return 1


def _get_infer_sem() -> threading.BoundedSemaphore:
    global _infer_sem
    with _lock:
        if _infer_sem is None:
            _infer_sem = threading.BoundedSemaphore(_bounded(_infer_cap(), 4))
        return _infer_sem


def _get_sam_sem() -> threading.BoundedSemaphore:
    global _sam_sem
    with _lock:
        if _sam_sem is None:
            _sam_sem = threading.BoundedSemaphore(_bounded(_sam_cap(), 1))
        return _sam_sem


@contextmanager
def acquire_infer_slot():
    sem = _get_infer_sem()
    sem.acquire()
    try:
        yield
    finally:
        sem.release()


@contextmanager
def acquire_sam_slot():
    sem = _get_sam_sem()
    sem.acquire()
    try:
        yield
    finally:
        sem.release()


__all__ = ["acquire_infer_slot", "acquire_sam_slot"]
