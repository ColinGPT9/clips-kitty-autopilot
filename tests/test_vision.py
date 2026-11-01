from types import SimpleNamespace

import pytest

from autopilot import vision
from autopilot.engine import models


def test_verified_model_cache_refuses_corrupt_download(tmp_path, monkeypatch):
    monkeypatch.setattr(models, "MANIFEST", {"fixture": {"name": "fixture.model", "sha256": "0" * 64, "url": "https://example.test/model"}})
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, size):
            return b""
    monkeypatch.setattr(models.urllib.request, "urlopen", lambda *args, **kwargs: Response())
    with pytest.raises(RuntimeError, match="checksum"):
        models.ensure("fixture", tmp_path)
    assert not (tmp_path / "fixture.model").exists()


def test_silent_game_character_is_not_used_as_webcam(tmp_path, monkeypatch):
    from autopilot.engine import detect
    monkeypatch.setattr(models, "ensure", lambda *args: tmp_path / "fixture")
    monkeypatch.setattr(detect, "find_cam", lambda *args, **kwargs: SimpleNamespace(camera=None, reason="no real speaker"))
    result = vision.camera(tmp_path / "source.mp4", tmp_path)
    assert result["camera"] is None
    assert result["detector"] == "yolov8n-pose + TalkNet"


def test_talknet_camera_is_refined_without_trimming(tmp_path, monkeypatch):
    from autopilot.engine import detect
    monkeypatch.setattr(models, "ensure", lambda *args: tmp_path / "fixture")
    face = SimpleNamespace(overlay=True, box=(0, 0, .3, .4))
    monkeypatch.setattr(detect, "find_cam", lambda *args, **kwargs: SimpleNamespace(camera=face, reason="speaking streamer"))
    monkeypatch.setattr(detect, "stills", lambda *args: [])
    monkeypatch.setattr(detect, "snap_to_frame", lambda box, frames: box)
    monkeypatch.setattr(detect, "head_in_box", lambda *args: (30, 10, 50))
    result = vision.camera(tmp_path / "source.mp4", tmp_path)
    assert result["camera"] == [0, 0, .3, .4]
    assert result["head"] == [30, 10, 50]


def test_fullscreen_speaker_does_not_trigger_gaming_split(tmp_path, monkeypatch):
    from autopilot.engine import detect
    monkeypatch.setattr(models, "ensure", lambda *args: tmp_path / "fixture")
    face = SimpleNamespace(overlay=False, box=(0, 0, 1, 1))
    monkeypatch.setattr(detect, "find_cam", lambda *args, **kwargs: SimpleNamespace(camera=face, reason="fullscreen camera"))
    assert vision.camera(tmp_path / "source.mp4", tmp_path)["camera"] is None
