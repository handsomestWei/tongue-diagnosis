"""JSON 行日志与请求上下文字段。"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any


class JsonLineFormatter(logging.Formatter):
    """单行 JSON，便于日志采集；兼容没有 extra 的记录。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # 来自 `logger.info(..., extra={...})` 的常见字段
        for k in ("request_id", "method", "path", "status_code", "duration_ms", "client"):
            v = getattr(record, k, None)
            if v is not None:
                payload[k] = v
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_structured_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if getattr(root, "_td_json_logging_configured", False):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLineFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    setattr(root, "_td_json_logging_configured", True)


__all__ = ["JsonLineFormatter", "configure_structured_logging"]
