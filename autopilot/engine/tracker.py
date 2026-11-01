"""Selected tracker primitives from Clips Kitty; see PROVENANCE.md."""
import threading
from dataclasses import dataclass, field
from pathlib import Path
import cv2
import numpy as np


_model = None  # loaded once per process; YOLO init is expensive


_infer_lock = threading.Lock()


_thread_local = threading.local()


def _get_model(model_name: str):
    global _model
    with _infer_lock:
        if _model is None:
            from ultralytics import YOLO  # lazy: heavy import, pulls in torch

            from .models import yolo_weights
            from .runtime import cuda_usable

            # Absolute path, not the bare name: ultralytics resolves a bare
            # name against the working directory and downloads it when that
            # misses. The engine is spawned without a working directory, so
            # that miss is guaranteed in a packaged build and the download
            # fails outright on a machine with no route to GitHub.
            _model = YOLO(yolo_weights(model_name))

            usable, reason = cuda_usable()
            if not usable:
                print(f"  Tracking: using CPU — {reason}")
            else:
                _model.to("cuda")
                # Prove the GPU before the whole job depends on it. Moving
                # weights launches no kernel, so .to("cuda") succeeds even on a
                # card this build has no code for, and the failure would
                # otherwise surface at the first predict() — thousands of
                # frames into someone's video, as a crash rather than a
                # fallback. One throwaway inference buys that back.
                #
                # Calls predict directly rather than _detect, which would
                # deadlock on the non-reentrant lock already held here.
                try:
                    _model.predict(np.zeros((32, 32, 3), np.uint8),
                                   device="cuda", verbose=False)
                except Exception as e:
                    _model.to("cpu")
                    print(f"  Tracking: GPU unusable ({str(e)[:90]}) — using CPU")
                else:
                    print(f"  Tracking: GPU (CUDA) active — {reason}")
    return _model


def _get_cascades():
    """The two Haar cascades, or None when they are not on this machine.

    Per-thread instances: detectMultiScale is not thread-safe on a shared one.

    Returns None rather than an unusable classifier. cv2.CascadeClassifier
    given a missing file does NOT raise — it hands back an empty classifier,
    and the error only appears later inside detectMultiScale as
    "(-215:Assertion failed) !empty()". That killed every render needing the
    face fallback in installed builds (#86) while working perfectly from a
    checkout, because the frozen app ships cv2 without its data directory.

    Resolved through core.binaries so the bundled copy is found in a packaged
    build, with cv2's own directory as the fallback for a checkout.
    """
    if getattr(_thread_local, "cascades_missing", False):
        return None

    cascades = getattr(_thread_local, "cascades", None)
    if cascades is None:
        from .binaries import haar_cascade

        paths = [
            haar_cascade("haarcascade_frontalface_default.xml"),
            haar_cascade("haarcascade_profileface.xml"),
        ]
        if not all(paths):
            _thread_local.cascades_missing = True
            print("      Face refinement unavailable (Haar cascades not found) "
                  "— cropping from pose detection only")
            return None

        # Both failure modes, because they are different and neither is
        # obvious: a MISSING file gives an empty classifier and no error, while
        # a file that exists but is not a cascade raises SystemError out of the
        # constructor. Checking .empty() alone still crashed on the second.
        try:
            loaded = tuple(cv2.CascadeClassifier(p) for p in paths)
            unusable = any(c.empty() for c in loaded)
        except Exception:
            unusable = True

        if unusable:
            _thread_local.cascades_missing = True
            print("      Face refinement unavailable (Haar cascades unreadable) "
                  "— cropping from pose detection only")
            return None

        cascades = loaded
        _thread_local.cascades = cascades
    return cascades


def _face_box(frame, box) -> tuple[int, int, int, int] | None:
    """Find the face inside a person box. In close-ups the person box centers
    on the torso, which can sit far from the face — the face box drives both
    framing and the talking detector.

    Detection order: frontal face -> left profile -> right profile (the
    profile cascade only knows one side, so the mirrored image covers the
    other). Returns the face box in absolute pixels, or None when no face is
    visible at all (e.g. subject facing away) — the caller then falls back
    to the person-box center, which is the best anyone can do without a face.
    """
    x1, y1, x2, y2 = (int(v) for v in box[:4])
    rx, ry = max(0, x1), max(0, y1)
    head_h = max((y2 - y1) // 2, 40)
    roi = frame[ry : y1 + head_h, rx:x2]
    if roi.size == 0:
        return None
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    cascades = _get_cascades()
    if cascades is None:
        # No face refinement available. The caller already handles "no face
        # found" — it falls back to the pose box — so this costs a little crop
        # precision rather than the whole clip.
        return None
    frontal, profile = cascades

    faces = frontal.detectMultiScale(gray, 1.15, 4, minSize=(36, 36))
    if len(faces) == 0:
        faces = profile.detectMultiScale(gray, 1.15, 4, minSize=(36, 36))
    if len(faces) == 0:
        flipped = profile.detectMultiScale(cv2.flip(gray, 1), 1.15, 4, minSize=(36, 36))
        if len(flipped) > 0:
            fx, fy, fw, fh = max(flipped, key=lambda f: f[2] * f[3])
            fx = gray.shape[1] - (fx + fw)  # mirror x back to the original
            faces = [(fx, fy, fw, fh)]
    if len(faces) == 0:
        return None
    fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])  # largest face
    return (rx + fx, ry + fy, rx + fx + fw, ry + fy + fh)


def head_box(head) -> tuple[int, int, int, int]:
    """A face-shaped box around the head the POSE model found.

    The pose model returns the head as (cx, cy, width) from the nose/eye/ear
    keypoints. Everything downstream — the mouth region, the ASD crop — wants
    a box, so this is the one place that conversion lives.

    It exists so the Haar cascade can be skipped. Haar costs 79-124 ms per
    call and was being run on every visible person on every sample, even when
    pose had ALREADY located the head: 63% of tracking time and 81% of podcast
    analysis, for a position that was then thrown away in favour of the pose
    keypoints. Pose finds a head on ~78% of detections, so most of that work
    was answering a question that was already answered.

    A SQUARE on purpose, and it must stay one: video/asd.py::_mouth_patch
    derives TalkNet's crop from this box's larger dimension, so changing the
    proportions moves what the model sees. Measured, making it taller changed
    the speaker verdicts on three of four bench clips. This is the shape the
    ASD fallback has always used and the shape its results were measured with.

    For mouth MOTION use mouth_region() instead — that needs a different shape,
    and the two are separate for exactly this reason.
    """
    cx, cy, hw = head
    half = hw / 2
    return (int(cx - half), int(cy - half), int(cx + half), int(cy + half))


_ASD_MIN_FACE_SAMPLES = 8    # a track needs this many face sightings to be


_ASD_MAX_TRACKS = 4          # crops are held in memory; four faces is already


_ASD_MAX_GAP = 0.6           # seconds: past this, a face box is too stale to


_ASD_SPEECH = 0.35           # ...and the clip must be this loud, relative to


def _clip_pcm(clip_path: Path, sr: int) -> "np.ndarray | None":
    """The clip's audio as mono float32. None when it has none."""
    import subprocess

    from .binaries import ffmpeg

    try:
        out = subprocess.run(
            [ffmpeg(), "-v", "error", "-i", str(clip_path),
             "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
            capture_output=True, timeout=300,
        )
        if out.returncode != 0 or not out.stdout:
            return None
        return np.frombuffer(out.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    except Exception as e:
        print(f"      (clip audio unavailable: {e})")
        return None


def _interp_boxes(seen: list, times: "np.ndarray") -> "np.ndarray | None":
    """A face box for every time in `times`, interpolated from the samples
    where the face was actually detected.

    `seen` is [(t, (x1, y1, x2, y2)), ...] in time order. Rows outside the
    track's own span, or across a gap longer than _ASD_MAX_GAP, come back NaN:
    the person is not there to be cropped, and a stale box would feed the
    model somebody else's face.
    """
    ts = np.array([s[0] for s in seen], dtype=np.float64)
    box = np.array([s[1] for s in seen], dtype=np.float64)
    out = np.empty((len(times), 4), dtype=np.float64)
    for k in range(4):
        out[:, k] = np.interp(times, ts, box[:, k])
    # np.interp clamps outside the range; NaN those, plus anything sitting in
    # a long gap between two sightings.
    nearest = np.abs(times[:, None] - ts[None, :]).min(axis=1)
    out[(times < ts[0]) | (times > ts[-1]) | (nearest > _ASD_MAX_GAP)] = np.nan
    return out


def _mouth_patch(frame, box, size: int):
    """The square TalkNet expects, cut from a COLOUR frame around `box`.

    Not the face box. TalkNet's own pipeline takes a region about 0.7x the
    face box, shifted DOWN so it is centred on the mouth rather than the eyes,
    which is what a lip-sync model is looking at. Feeding it a plain face crop
    is feeding it a different picture than it was trained on.

    Out-of-frame edges are padded with mid-grey (110) exactly as upstream does
    — clipping instead would squash the face when someone reaches the edge of
    the shot, and a squashed face is a face the model has never seen.

    It takes the COLOUR frame and converts only the slice it keeps. The caller
    used to greyscale the whole 1920x1080 frame and hand that in, to read four
    regions of about 150x150 out of it. Greyscale is per-pixel, so the patch is
    bit-identical either way — but measured over 500 frames, converting the
    frame costs 2.39 CPU-seconds against 0.05 for converting just the faces.
    51x, and OpenCV spread it across 9.4 cores to do it. With three clips
    rendering at once that was most of why the machine became unusable.
    """
    if np.isnan(box[0]):
        return None
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    bs = max(box[2] - box[0], box[3] - box[1]) / 2
    if bs < 6:
        return None
    half = 0.7 * bs
    cy += 0.4 * bs           # down onto the mouth
    x0, y0 = int(round(cx - half)), int(round(cy - half))
    side = max(8, int(round(2 * half)))

    h, w = frame.shape[:2]
    patch = np.full((side, side), 110, dtype=np.uint8)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(w, x0 + side), min(h, y0 + side)
    if sx1 - sx0 < 4 or sy1 - sy0 < 4:
        return None
    patch[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = cv2.cvtColor(
        frame[sy0:sy1, sx0:sx1], cv2.COLOR_BGR2GRAY
    )
    return cv2.resize(patch, (size, size))


def _contested_spans(mask, fps: int, n: int, window: int | None = None) -> list:
    """The stretches worth scoring, as (start, end) frame indices.

    `mask` marks frames where two or more people are on screen. Runs shorter
    than a second are grown to a second and near neighbours are merged,
    because the model's shortest window is a second and a run of six frames
    would otherwise be scored on padding.

    `window`, when given, takes the place of `fps` throughout: the shortest
    stretch, and the gap that joins two. Only the podcast path sets it, to 26:
    asd.score_track returns all zeros for a stretch of exactly 25 frames (the
    audio of N frames gives N - 1 frames of MFCCs, under its one-second
    minimum), so every stretch grown to 25 gets no verdict. Left at None it is
    `fps`, as the stream tracker has always had it.
    """
    if window is not None:
        fps = window
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    gap = fps  # a second apart or less: one span, not two
    breaks = np.flatnonzero(np.diff(idx) > gap)
    starts = np.r_[idx[0], idx[breaks + 1]]
    ends = np.r_[idx[breaks], idx[-1]] + 1

    spans = []
    for a, b in zip(starts, ends):
        a, b = int(a), int(b)
        if b - a < fps:
            a = max(0, a - (fps - (b - a)) // 2)
            b = min(n, a + fps)
            a = max(0, b - fps)
        if spans and a <= spans[-1][1]:      # grew into its neighbour
            spans[-1] = (spans[-1][0], b)
        else:
            spans.append((a, b))
    return [(a, b) for a, b in spans if b - a >= fps]


@dataclass
class _Track:
    box: tuple                     # last (x1, y1, x2, y2, conf, head) in pixels
    last_t: float
    dominance: float = 0.0         # EMA of confidence x area
    speak: float = 0.0             # EMA of mouth-region motion (talking proxy)
    prev_mouth: object = None      # last mouth crop (np array) for motion diff
    face_rate: float = 0.0         # EMA of "was a face detected this sample?"
    face_offset: float = 0.0       # EMA of (face cx - body cx), normalized
    face_w: float = 0.0            # EMA of face box width, normalized
    head_rate: float = 0.0         # EMA of "pose head keypoints seen this sample?"
    head_offset: float = 0.0       # EMA of (head cx - body cx), normalized
    head_cys: list = field(default_factory=list)  # normalized head center-y history
    n_seen: int = 0
    centers: list = field(default_factory=list)   # normalized cx history
    areas: list = field(default_factory=list)     # area fraction history
    norm_boxes: list = field(default_factory=list)  # normalized (x1, y1, x2, y2)


def _detect(model, frame, min_confidence) -> list[tuple]:
    """Person detections as (x1, y1, x2, y2, conf, head). With a pose model,
    head is (head_cx_px, head_cy_px, head_w_px) from the nose/eye/ear keypoints — the most
    reliable "where is the head" signal there is (needs no visible face). With
    a plain detection model, head is None and the Haar face box fills in."""
    from .runtime import torch_device

    with _infer_lock:
        # device= is not optional. Without it ultralytics calls
        # select_device(''), which auto-selects the first available GPU and
        # silently undoes the CPU decision _get_model just made.
        results = model.predict(frame, classes=[0], conf=min_confidence,
                                device=torch_device(), verbose=False)
    out = []
    for r in results:
        kp = getattr(r, "keypoints", None)
        kxy = kp.xy.tolist() if kp is not None and kp.xy is not None else None
        kconf = kp.conf.tolist() if kp is not None and kp.conf is not None else None
        for i, b in enumerate(r.boxes):
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            head = None
            if kxy is not None and kconf is not None and i < len(kxy):
                # COCO keypoints 0-4: nose, eyes, ears.
                pts = [kxy[i][j] for j in range(5) if kconf[i][j] > 0.5]
                if pts:
                    head_cx = sum(p[0] for p in pts) / len(pts)
                    head_cy = sum(p[1] for p in pts) / len(pts)
                    xs = [p[0] for p in pts]
                    spread = max(xs) - min(xs)
                    head_w = max(spread * 1.6, (y2 - y1) * 0.12)
                    head = (head_cx, head_cy, head_w)
            out.append((x1, y1, x2, y2, float(b.conf[0]), head))
    return out


def _assign(tracks: dict, detections: list, t: float) -> list[int]:
    """Greedy IoU matching of detections to live tracks; unmatched detections
    start new tracks. Returns the track ids visible in this frame."""
    pairs = []
    for tid, tr in tracks.items():
        if t - tr.last_t > 2.0:
            continue  # stale track — don't revive identities after long gaps
        for i, d in enumerate(detections):
            iou = _iou(tr.box[:4], d[:4])
            if iou >= 0.25:
                pairs.append((iou, tid, i))

    visible, used_t, used_d = [], set(), set()
    for _, tid, i in sorted(pairs, key=lambda p: p[0], reverse=True):
        if tid in used_t or i in used_d:
            continue
        tracks[tid].box = detections[i]
        tracks[tid].last_t = t
        visible.append(tid)
        used_t.add(tid)
        used_d.add(i)

    for i, d in enumerate(detections):
        if i not in used_d:
            tid = max(tracks, default=-1) + 1
            tracks[tid] = _Track(box=d, last_t=t)
            visible.append(tid)
    return visible


def _iou(a, b) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)
