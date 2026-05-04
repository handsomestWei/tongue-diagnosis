import numpy as np

from core.preprocess_classify import preprocess_for_classify


def test_closeup_skips_sam():
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    img[:, :] = (10, 20, 30)
    r = preprocess_for_classify(img, "tongue_closeup", out_size=32)
    assert not r.sam_called
    assert r.tensor_bgr.shape == (32, 32, 3)


def test_full_face_calls_sam_provider():
    img = np.zeros((80, 100, 3), dtype=np.uint8)

    def provider():
        return [10.0, 10.0, 50.0, 50.0]

    r = preprocess_for_classify(
        img,
        "full_face_selfie",
        sam_box_provider=provider,
        out_size=48,
        clahe=False,
        unsharp=False,
    )
    assert r.sam_called
    assert not r.sam_failed
    assert r.tensor_bgr.shape == (48, 48, 3)
