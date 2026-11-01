"""Resolve standard FFmpeg tools without importing the desktop app."""
import os
import shutil


def ffmpeg():
    return os.environ.get("FFMPEG_BINARY") or shutil.which("ffmpeg") or "ffmpeg"


def ffprobe():
    return os.environ.get("FFPROBE_BINARY") or shutil.which("ffprobe") or "ffprobe"
