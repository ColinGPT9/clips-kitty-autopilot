"""Isolated CPU model process: release detector memory before Whisper/FFmpeg."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .engine import models


def camera(source, model_directory):
    from .engine import detect
    with models.directory(model_directory):
        pose = models.ensure("yolo", model_directory)
        models.ensure("talknet", model_directory)
        finding = detect.find_cam(Path(source), str(pose))
        face = finding.camera
        result = {"camera": None, "head": None, "reason": finding.reason,
                  "detector": "yolov8n-pose + TalkNet"}
        if face is not None and face.overlay:
            box = detect.snap_to_frame(face.box, detect.stills(Path(source)))
            result["camera"] = list(box)
            head = detect.head_in_box(Path(source), box, str(pose))
            result["head"] = list(head) if head is not None else None
        return result


def check_camera(model_directory):
    """Real CPU inference on synthetic fixtures; no live Twitch observations."""
    import numpy as np

    from .engine import asd, tracker
    with models.directory(model_directory):
        models.ensure("talknet")
        model = tracker._get_model("yolov8n-pose.pt")
        tracker._detect(model, np.zeros((180, 320, 3), dtype=np.uint8), .4)
        faces = np.full((151, asd.FACE_SIZE, asd.FACE_SIZE), 110, dtype=np.uint8)
        times = np.arange(round(151 / asd.FPS * asd.AUDIO_SR)) / asd.AUDIO_SR
        pcm = (.1 * np.sin(2 * np.pi * 440 * times)).astype(np.float32)
        scores = asd.score_track(faces, pcm)
        if len(scores) != len(faces) or not np.isfinite(scores).all():
            raise RuntimeError("TalkNet inference check failed")
    return {"synthetic_fixture": True, "yolov8_cpu": True, "talknet_cpu": True, "frames": len(scores)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["camera", "captions", "check-camera"])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--models", required=True, type=Path)
    parser.add_argument("--duration", type=float, default=0)
    args = parser.parse_args()
    os.environ["AUTOPILOT_MODEL_DIR"] = str(args.models.resolve())
    os.environ.setdefault("YOLO_CONFIG_DIR", str(args.models / "ultralytics"))
    import cv2
    cv2.setNumThreads(2)
    if args.operation in ("camera", "check-camera"):
        import torch
        torch.set_num_threads(2)
        torch.set_num_interop_threads(1)
        result = camera(args.source, args.models) if args.operation == "camera" else check_camera(args.models)
        try:
            import resource
            result["peak_rss_mib"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
        except ImportError:
            pass
        args.output.write_text(json.dumps(result), encoding="utf-8")
    else:
        from .media import _write_captions
        _write_captions(args.source, args.output.parent, args.duration, args.models)


if __name__ == "__main__":
    main()
