"""极简全局限流：按客户端 IP（或 X-Forwarded-For 首个）计数的滑动窗口。"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Deque

from fastapi import Request
from starlette.responses import JSONResponse

from api.config import get_settings

_lock = threading.Lock()
_windows: dict[str, Deque[float]] = {}


def _client_key(request: Request) -> str:
    xf = request.headers.get("x-forwarded-for")
    if xf:
        return xf.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    return request.client.host if request.client else "unknown"


def rate_limited_response(retry_after_sec: int) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "请求过于频繁，请稍后再试"},
        headers={"Retry-After": str(retry_after_sec)},
    )


def check_rate_limit(request: Request) -> JSONResponse | None:
    s = get_settings()
    rpm = int(s.rate_limit_per_minute)
    if rpm <= 0:
        return None
    now = time.monotonic()
    window_sec = 60.0
    key = _client_key(request)
    with _lock:
        dq = _windows.setdefault(key, deque())
        while dq and (now - dq[0]) > window_sec:
            dq.popleft()
        if len(dq) >= rpm:
            oldest = dq[0]
            retry = max(1, int(window_sec - (now - oldest)) + 1)
            return rate_limited_response(retry)
        dq.append(now)
    return None
