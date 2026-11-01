"""Verified, persistent public model downloads. No user credentials are used."""
from __future__ import annotations

import hashlib
import os
import urllib.request
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_directory = ContextVar("model_directory", default=None)
MANIFEST = {
    "talknet": {"name": "pretrain_TalkSet.model",
                "sha256": "d985ddd07dca08864a28337726f5b7d91b6426bebc7327f0e9b21cf9ff1cc937",
                "url": "https://huggingface.co/Kestroll/talknet-asd/resolve/main/pretrain_TalkSet.model"},
    "yolo": {"name": "yolov8n-pose.pt",
             "sha256": "c6fa93dd1ee4a2c18c900a45c1d864a1c6f7aba75d84f91648a30b7fb641d212",
             "url": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n-pose.pt"},
}


def cache_dir():
    return Path(_directory.get() or os.environ.get("AUTOPILOT_MODEL_DIR") or Path(os.environ.get("DATA_DIR", "data")) / "models").resolve()


@contextmanager
def directory(path):
    token = _directory.set(Path(path).resolve())
    try:
        yield
    finally:
        _directory.reset(token)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def ensure(identifier, root=None):
    model = MANIFEST[identifier]
    target = Path(root or cache_dir()) / model["name"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and digest(target) == model["sha256"]:
        return target
    temporary = target.with_suffix(target.suffix + ".partial")
    try:
        request = urllib.request.Request(model["url"], headers={"User-Agent": "Clips-Kitty-Autopilot/0.1"})
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as stream:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 200 * 1024 * 1024:
                    raise RuntimeError("Model download exceeded the size limit")
                stream.write(chunk)
        if digest(temporary) != model["sha256"]:
            raise RuntimeError("Model checksum verification failed")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def yolo_weights(name):
    expected = cache_dir() / MANIFEST["yolo"]["name"]
    if str(name) not in (MANIFEST["yolo"]["name"], str(expected)):
        raise ValueError("Only the verified YOLOv8n pose model is supported")
    return str(ensure("yolo"))
