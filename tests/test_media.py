import json
import subprocess

import pytest

from autopilot import media
from autopilot.engine.binaries import ffmpeg


@pytest.mark.media
@pytest.mark.parametrize("audio,camera", [(False, None), (True, None), (True, [0, 0, .3, .4])])
def test_whole_render_retains_video_when_audio_ends_early(tmp_path, audio, camera):
    source = tmp_path / "source.mp4"
    cmd = [ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=5:duration=2"]
    if audio:
        cmd += ["-f", "lavfi", "-i", "sine=frequency=440:duration=0.4", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(source)]
    subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    target = tmp_path / "output.mp4"
    result = media.render_whole(source, target, {"captions": False, "detect_camera": False, "camera": camera})
    assert (result["width"], result["height"]) == (1080, 1920)
    assert abs(result["duration"] - 2) < .15
    assert result["has_audio"] == audio
    assert result["whole"] is True
    assert json.loads(target.with_suffix(".json").read_text())["source_duration"] == 2
    subprocess.run([ffmpeg(), "-v", "error", "-i", str(target), "-f", "null", "-"],
                   check=True, capture_output=True, timeout=30)


def test_caption_failure_does_not_silently_publish_without_captions(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "probe", lambda path: {"width": 320, "height": 180, "duration": 2, "has_audio": True})
    def fail(*args, **kwargs):
        raise RuntimeError("fixture unavailable model")
    monkeypatch.setattr(media, "captions", fail)
    with pytest.raises(RuntimeError):
        media.render_whole(tmp_path / "fixture.mp4", tmp_path / "output.mp4", {"captions": True, "detect_camera": False})
    assert not (tmp_path / "output.mp4").exists()


def test_gaming_captions_clear_the_gameplay_region():
    from autopilot.engine import layout
    plan = layout.plan(1920, 1080, {"cam": [0, 0, .25, .37], "preset": "half",
                                    "game_fit": "fit", "game_box": [0, 0, 1, 1]})
    margin = media.caption_margin(plan)
    baseline = 1920 - margin
    assert baseline <= plan.element("game").dest[1] - 30
    assert baseline > plan.element("cam").dest[1]


def test_whole_source_fit_keeps_bottom_safe_caption_position():
    from autopilot.engine import layout
    plan = layout.plan(1920, 1080, {"cam": None, "preset": "blurred", "game_box": [0, 0, 1, 1]})
    assert media.caption_margin(plan) == 210


@pytest.mark.media
def test_whole_gaming_excludes_webcam_from_game_panel(tmp_path, monkeypatch):
    """The red source webcam appears only in its own band, as in Clips Kitty."""
    source = tmp_path / "source.mp4"
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i",
                    "color=blue:size=320x180:rate=5:duration=1,drawbox=x=0:y=0:w=80:h=70:color=red:t=fill",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source)],
                   check=True, capture_output=True, timeout=30)
    plans = []
    original = media.compose.render

    def capture_plan(source, target, plan, **kwargs):
        plans.append(plan)
        return original(source, target, plan, **kwargs)

    monkeypatch.setattr(media.compose, "render", capture_plan)
    target = tmp_path / "vertical.mp4"
    result = media.render_whole(source, target, {"camera": [0, 0, .25, 70 / 180], "captions": False})
    game = plans[0].element("game")
    x, y, w, h = game.src
    assert x >= 80 or y >= 70, "The gameplay crop still includes the source webcam"
    assert result["whole"] is True
    assert abs(result["duration"] - 1) < .15
    import numpy as np

    pixels = subprocess.check_output([ffmpeg(), "-v", "error", "-i", str(target),
                                      "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    frame = np.frombuffer(pixels, dtype=np.uint8).reshape(1920, 1080, 3)
    dx, dy, dw, dh = game.dest
    game_pixels = frame[dy + 4:dy + dh - 4, dx + 4:dx + dw - 4]
    red = (game_pixels[:, :, 0] > 150) & (game_pixels[:, :, 1] < 80) & (game_pixels[:, :, 2] < 80)
    assert red.mean() < .001, "A second red webcam is visible inside the gameplay"
