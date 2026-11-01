# Reused gaming camera regression tests; see PROVENANCE.md.
"""Gaming / Split-Screen: who the streamer is, and where each band comes from.

The two rules this pins down:
- TalkNet decides who the streamer is. A bigger face (a game character, a
  portrait, the person in a video being reacted to) never wins on size.
- The game band is a fixed crop that only moves to stay clear of the webcam
  or where the user put it. Nothing picks a region by how much it moves.
"""


import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("cv2")

from autopilot.engine import detect  # noqa: E402

# ---- who the streamer is -------------------------------------------------------------


def _faces(n=250, loud=None, **logits):
    """{tid: Face} from constant (or given) TalkNet logits over n frames."""
    loud = np.ones(n, dtype=bool) if loud is None else loud
    faces = {}
    for tid, value in logits.items():
        scores = value if isinstance(value, np.ndarray) else np.full(n, value, dtype=np.float32)
        share, conf = detect.speaking(scores, loud)
        faces[tid] = detect.Face((0.0, 0.0, 0.2, 0.3), 1.0, share, conf, True)
    return faces


def test_the_speaking_face_wins_even_when_a_bigger_one_is_on_screen():
    # "big" is a game character filling the screen (silent), "cam" the small webcam face
    faces = _faces(big=-4.0, cam=0.5)
    faces["big"].box = (0.2, 0.0, 0.6, 1.0)
    assert detect.pick_streamer(faces) == "cam"
    assert faces["big"].speaking_share == 0.0


def test_a_lone_face_is_the_streamer_only_if_it_is_speaking():
    assert detect.pick_streamer(_faces(only=0.2)) == "only"
    assert detect.pick_streamer(_faces(only=-4.0)) is None


def test_when_two_faces_speak_the_most_confident_one_wins():
    """A watch party: the streamer and the person in the video both talk for
    the whole clip. TalkNet is far surer of the one in sync with the stream's
    audio (measured: 3.3 against 0.3), whichever comes first or is bigger."""
    assert detect.pick_streamer(_faces(video=0.3, streamer=3.3)) == "streamer"


def test_only_loud_moments_count():
    scores = np.full(250, -4.0, dtype=np.float32)
    scores[:50] = 1.0               # "speaking" only during silence
    loud = np.ones(250, dtype=bool)
    loud[:50] = False
    assert detect.pick_streamer(_faces(loud=loud, only=scores)) is None


def test_frames_a_face_is_off_screen_dont_count_against_it():
    scores = np.full(250, 0.4, dtype=np.float32)
    scores[:200] = -np.inf          # on screen for the last fifth only, speaking throughout
    assert detect.pick_streamer(_faces(only=scores)) == "only"


def _track(times, box=(100, 60, 380, 330), cx=0.12):
    tr = detect.Track()
    for i, t in enumerate(times):
        tr.times.append(t)
        tr.person.append(box)
        tr.seen.append((t, box))
        tr.head_cx.append(cx[i % len(cx)] if isinstance(cx, list) else cx)
    return tr


def test_a_face_seen_for_a_moment_is_not_a_candidate():
    """Measured in a GTA roleplay stream: a driver glimpsed through a car
    window for 3% of a clip got TalkNet's full speaking score. Only a face on
    screen for most of the clip can be the streamer."""
    tracks = {0: _track([i / 8 for i in range(300)]), 1: _track([i / 8 for i in range(10)])}
    assert detect.candidates(tracks, 320) == [0]


def test_a_webcam_face_split_into_two_tracks_is_one_person():
    first = _track([i / 8 for i in range(150)])
    second = _track([20 + i / 8 for i in range(150)])      # same spot, identity lost at 19 s
    elsewhere = _track([i / 8 for i in range(150)], box=(1400, 100, 1800, 900))
    merged = detect.merge_tracks({0: first, 1: second, 2: elsewhere})
    assert len(merged) == 2
    assert detect.candidates(merged, 320)[0] in merged and len(merged[detect.candidates(merged, 320)[0]].times) == 300


def test_two_people_side_by_side_are_not_merged():
    a = _track([i / 8 for i in range(150)])
    b = _track([i / 8 for i in range(150)])                # same box, but on screen together
    assert len(detect.merge_tracks({0: a, 1: b})) == 2


def test_a_speaker_inside_a_small_box_is_an_overlay():
    box, overlay = detect.webcam_box(_track(range(60), cx=[0.12, 0.13, 0.11, 0.15, 0.09]), 1920, 1080)
    assert overlay is True
    x, y, w, h = box
    assert 0 <= x < 0.06 and w < 0.2 and h < 0.4


def test_a_camera_filling_the_frame_is_not_an_overlay():
    assert detect.webcam_box(_track(range(60), box=(300, 50, 1700, 1080), cx=0.5), 1920, 1080)[1] is False
    roaming = _track(range(60), box=(100, 300, 300, 800), cx=[0.1, 0.5, 0.9, 0.3, 0.7])
    assert detect.webcam_box(roaming, 1920, 1080)[1] is False


def _frames(n=6, cam=(0, 372, 160, 540), seed=1):
    """960x540 greyscale stills: a noisy game, a flat chat panel right of a
    webcam in the bottom-left corner, the webcam's picture changing."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        f = rng.integers(40, 120, (540, 960)).astype(np.uint8)          # the game, never still
        f[372:, 160:800] = 20                                           # chat panel beside the webcam
        x1, y1, x2, y2 = cam
        f[y1:y2, x1:x2] = rng.integers(150, 230, (y2 - y1, x2 - x1))    # the webcam picture
        out.append(f)
    return out


def test_the_streamers_box_grows_to_just_inside_the_webcams_border():
    """Measured on a speedrun: a margin around the streamer ran past the
    webcam into the chat panel beside it, and the clip showed a strip of chat
    down the side of the webcam. Now the box grows from the streamer out to
    the webcam's own border, and stops just inside it."""
    streamer = (0.0, 0.72, 0.15, 0.28)                 # true webcam: x 0-160 of 960, y 372-540 of 540
    x, y, w, h = detect.snap_to_frame(streamer, _frames())
    inset = detect.SNAP_INSET
    assert x == 0.0 and y + h == pytest.approx(1.0)    # frame edges stay put
    assert 160 / 960 - inset - 0.003 <= x + w <= 160 / 960       # inside the chat border
    assert 372 / 540 <= y <= 372 / 540 + inset + 0.004           # inside the top border


def test_a_streamer_box_a_few_pixels_past_the_border_comes_back_inside():
    """Measured on a survival game: the person box ran 5 px below the webcam
    into the chat under it. A border that close inside is still the edge."""
    x, _y, w, _h = detect.snap_to_frame((0.0, 0.72, 163 / 960, 0.28), _frames())
    assert x + w <= 160 / 960


def test_nothing_beside_the_webcam_gets_into_its_box():
    """A chat panel's edge further out is stronger than the webcam's own
    border; the nearest border wins, so the chat never comes in."""
    frames = _frames()
    for f in frames:
        f[372:, 230:232] = 255                         # a bright line past the webcam, inside the chat
    x, _y, w, _h = detect.snap_to_frame((0.0, 0.72, 0.15, 0.28), frames)
    assert x + w <= 160 / 960


def test_a_line_inside_the_streamers_own_box_is_not_the_border():
    """Measured: a door frame behind the streamer pulled the box's edge in
    across them. Sides only ever move out from the streamer."""
    frames = _frames(cam=(0, 300, 400, 540))
    for f in frames:
        f[300:, 250:] = 240                            # a bright doorway in the room behind them
    box = (0.0, 0.54, 0.43, 0.46)                      # webcam 0-400, streamer's box well past 250
    x, _y, w, _h = detect.snap_to_frame(box, frames)
    assert x + w > 0.4


def test_a_box_with_no_clear_border_is_left_as_it_was():
    rng = np.random.default_rng(2)
    noise = [rng.integers(0, 255, (540, 960)).astype(np.uint8) for _ in range(6)]
    box = (0.3, 0.3, 0.2, 0.3)
    assert detect.snap_to_frame(box, noise) == box
    assert detect.snap_to_frame(box, []) == box


# ---- the webcam for the whole video ---------------------------------------------------


def _clip(streamer_box=None, confidence=2.0, others=()):
    faces = {}
    if streamer_box:
        faces["s"] = detect.Face(streamer_box, 0.9, 1.0, confidence, True)
    for i, box in enumerate(others):
        faces[f"o{i}"] = detect.Face(box, 0.9, 0.2, -2.0, True)
    return detect.ClipFinding(faces, "s" if streamer_box else None)


CORNER = (0.0, 0.66, 0.25, 0.34)


def test_in_a_reaction_the_streamer_is_who_speaks_from_the_same_spot_all_video():
    """Measured on a reaction stream: the person in the watched video out-talked
    the streamer in one clip. Across the video the streamer speaks from the
    same corner again and again; the people in the content come and go."""
    findings = [
        _clip((0.69, 0.3, 0.16, 0.68), others=[CORNER]),   # the video's subject wins this one
        _clip(CORNER),
        _clip((0.01, 0.65, 0.24, 0.35)),
    ]
    cam = detect.video_cam(findings)
    assert cam is not None and cam[0] < 0.05 and cam[1] > 0.6
    assert detect.on_screen(cam, findings[0])                 # the webcam is there in clip 1 too


def test_one_vote_among_several_clips_is_not_a_webcam():
    assert detect.video_cam([_clip((0.4, 0.4, 0.1, 0.4)), _clip(), _clip()]) is None


def test_a_single_clip_decides_for_itself():
    assert detect.video_cam([_clip(CORNER)]) == CORNER


def test_a_game_character_in_the_same_spot_is_not_a_webcam():
    """Measured on a 3D visual novel: a character sat at the same desk for two
    clips and lip-flapped to the voice acting (TalkNet -0.6 and -0.4). Real
    webcams reached 0.3 to 3.4 in at least one clip."""
    desk = (0.29, 0.31, 0.14, 0.39)
    assert detect.video_cam([_clip(desk, -0.58), _clip(desk, -0.44), _clip()]) is None
    assert detect.video_cam([_clip(CORNER, -0.5), _clip(CORNER, 0.3), _clip()]) is not None


def test_a_vtuber_avatar_is_never_the_webcam():
    """Gaming mode is for people on camera; VTubers are not supported. Measured
    on two VTuber streams: the avatar sat in the same corner in every clip and
    lip-synced to the voice, but TalkNet never got above -0.35 on it. It must
    stay that way: the game fills the screen."""
    avatar = (0.61, 0.5, 0.38, 0.5)
    assert detect.video_cam([_clip(avatar, -0.35), _clip(avatar, -0.73), _clip(avatar, -0.98)]) is None


def test_a_camera_filling_the_frame_never_votes_for_a_split():
    full = detect.ClipFinding({"s": detect.Face((0.2, 0.0, 0.6, 1.0), 1.0, 1.0, 2.0, False)}, "s")
    assert detect.video_cam([full, full]) is None
