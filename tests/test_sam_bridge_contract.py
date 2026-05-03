from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

from core.sam_bridge import run_tonguesam_get_mask_box


def test_run_tonguesam_invokes_predict_with_visual_off_and_reads_json(tmp_path):
    root = tmp_path / "sam"
    for sub in ("data/test_in", "data/test_roi", "data/test_out"):
        (root / sub).mkdir(parents=True)
    (root / "predict.py").write_text("# noop\n", encoding="utf-8")

    img = root / "in.png"
    img.write_bytes(b"x")

    def fake_run(cmd, cwd=None, capture_output=False, text=False, timeout=None, check=False, env=None):
        cwd_p = Path(cwd or ".")
        assert cmd[0] == sys.executable
        assert cmd[1] == str(cwd_p / "predict.py")
        merged = {**__import__("os").environ, **(env or {})}
        assert merged.get("TONGUESAM_WRITE_VISUAL") == "0"
        # 模拟 predict.py：为 test_in 中唯一文件写出 ROI JSON
        ts_in = cwd_p / "data" / "test_in"
        ts_roi = cwd_p / "data" / "test_roi"
        files = [p for p in ts_in.iterdir() if p.is_file()]
        assert len(files) == 1
        stem = files[0].stem
        rec = {"box_mask_xyxy": [1, 2, 30, 40], "format": "xyxy", "space": "original_image_pixels"}
        (ts_roi / f"{stem}.json").write_text(json.dumps(rec), encoding="utf-8")
        return __import__("subprocess").CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    with patch("core.sam_bridge.subprocess.run", side_effect=fake_run):
        box = run_tonguesam_get_mask_box(img, root, timeout_sec=30)
    assert box == [1.0, 2.0, 30.0, 40.0]
