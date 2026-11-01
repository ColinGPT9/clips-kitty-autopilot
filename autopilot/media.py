"""Whole-clip media processing using the disclosed Clips Kitty Gaming library."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from .engine import compose, layout
from .engine.binaries import ffprobe


def probe(path):
    result = subprocess.run([ffprobe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                            capture_output=True, text=True, timeout=30, check=True)
    info = json.loads(result.stdout)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    return {"width": video["width"], "height": video["height"],
            "duration": float(info["format"]["duration"]),
            "has_audio": any(s["codec_type"] == "audio" for s in info["streams"])}


def download(clip_id, directory):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", clip_id):
        raise ValueError("Invalid Twitch clip ID")
    from yt_dlp import YoutubeDL
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "source.mp4"
    if target.exists():
        probe(target)
        return target
    options = {"quiet": True, "no_warnings": True, "noplaylist": True,
               "format": "best[ext=mp4]/best", "outtmpl": str(directory / "source.%(ext)s"),
               "socket_timeout": 30, "retries": 2, "max_filesize": 200 * 1024 * 1024}
    try:
        with YoutubeDL(options) as reader:
            result = reader.extract_info("https://clips.twitch.tv/" + clip_id, download=True)
            source = Path(reader.prepare_filename(result))
        if source.resolve().parent != directory.resolve():
            raise ValueError("Unexpected download path")
        probe(source)
        return source
    except Exception:
        raise RuntimeError("Twitch clip download failed. Check that the source is still available.") from None


def _model_step(operation, source, output, model_directory, duration=0):
    import sys
    output = Path(output)
    output.unlink(missing_ok=True)
    command = [sys.executable, "-m", "autopilot.vision", operation, str(Path(source).resolve()),
               str(output.resolve()), "--models", str(Path(model_directory).resolve()),
               "--duration", str(duration)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=1800,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if result.returncode or not output.is_file():
        raise RuntimeError(f"{operation.title()} processing failed. Check model downloads and available memory.")
    return output


def _camera(source, directory, model_directory):
    result = _model_step("camera", source, Path(directory) / "camera.json", model_directory)
    return json.loads(result.read_text(encoding="utf-8"))


def captions(source, directory, duration):
    return _model_step("captions", source, Path(directory) / "captions.ass",
                       Path(directory).parent.parent / "models", duration)


def _ass_time(seconds):
    value = max(0, round(seconds * 100))
    return f"{value // 360000}:{value // 6000 % 60:02}:{value // 100 % 60:02}.{value % 100:02}"


def _write_captions(source, directory, duration, model_directory):
    from faster_whisper import WhisperModel
    model_name = os.environ.get("WHISPER_MODEL", "base.en")
    model = WhisperModel(model_name, device="cpu", compute_type="int8",
                         download_root=str(model_directory), cpu_threads=2, num_workers=1)
    segments, _ = model.transcribe(str(source), word_timestamps=True, vad_filter=True)
    words = []
    for segment in segments:
        if segment.words:
            words.extend((w.start, w.end, w.word.strip()) for w in segment.words if w.word.strip())
        elif segment.text.strip():
            words.append((segment.start, segment.end, segment.text.strip()))
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,64,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,65,65,210,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for index in range(0, len(words), 3):
        group = words[index:index + 3]
        start, stop = max(0, group[0][0]), min(duration, group[-1][1])
        text = " ".join(w[2] for w in group).replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ")
        if stop > start:
            lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(stop)},Default,,0,0,0,,{text}\n")
    target = Path(directory) / "captions.ass"
    target.write_text("".join(lines), encoding="utf-8")
    return target


def render_whole(source, target, options=None):
    source, target = Path(source), Path(target)
    options = options or {}
    facts = probe(source)
    if not 0 < facts["duration"] <= 180:
        raise ValueError("This app accepts whole Twitch clips up to three minutes.")
    target.parent.mkdir(parents=True, exist_ok=True)
    work = target.parent / (target.stem + "-work")
    work.mkdir(exist_ok=True)
    cam = options.get("camera")
    detection = {"camera": cam, "head": None, "detector": "manual" if cam else "off"}
    if cam is None and options.get("detect_camera", True):
        detection = _camera(source, work, target.parent.parent / "models")
        cam = detection["camera"]
    settings = {"cam": cam, "preset": "half" if cam else "blurred", "order": "cam_top",
                "game_fit": "fit", "game_box": [0, 0, 1, 1]}
    plan = layout.plan(facts["width"], facts["height"], settings,
                       {"cam": detection["head"]} if cam and detection.get("head") else {})
    ass = captions(source, work, facts["duration"]) if options.get("captions", True) and facts["has_audio"] else None
    temporary = target.with_name(target.stem + ".partial.mp4")
    try:
        compose.render(source, temporary, plan, ass_path=ass)
        result = probe(temporary)
        if (result["width"], result["height"]) != (1080, 1920) or abs(result["duration"] - facts["duration"]) > .15:
            raise ValueError("Whole-clip output verification failed")
        os.replace(temporary, target)
    except Exception:
        raise RuntimeError("Whole-clip rendering failed. The source is retained for inspection.") from None
    metadata = {**result, "source_duration": facts["duration"], "layout": plan.kind,
                "whole": True, "captions": ass is not None, "camera": cam,
                "detector": detection["detector"], "path": str(target)}
    target.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
