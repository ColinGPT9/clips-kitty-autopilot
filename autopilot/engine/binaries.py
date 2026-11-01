"""Resolve standard FFmpeg tools without importing the desktop app."""
import os
import shutil


def ffmpeg():
    return os.environ.get("FFMPEG_BINARY") or shutil.which("ffmpeg") or "ffmpeg"


def ffprobe():
    return os.environ.get("FFPROBE_BINARY") or shutil.which("ffprobe") or "ffprobe"


def haar_cascade(filename):
    import cv2
    from pathlib import Path
    path = Path(cv2.data.haarcascades) / filename
    return str(path) if path.is_file() else None
