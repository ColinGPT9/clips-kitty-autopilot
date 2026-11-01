# Source provenance

Used as starter template / foundation: [Clips Kitty](https://github.com/ColinGPT9/clips-studio), a pre-existing open-source application. This independent repository reuses its provider adapters and result/error contracts as a library. It is not a GitHub fork.

The upstream application predates the hackathon. Its Twitch Clips/Autopilot additions were developed October 30-31, 2026. This standalone web application is assembled November 1, 2026. Reused code is not claimed as newly authored here; fresh repository history does not erase its origin. Eligibility is determined by the organizers.

Upstream source snapshot: `cc1bcbc0aa5b6d518959e3daaac16545b21ff740`. The original GNU AGPL v3 license is retained.

| Upstream | Local library |
|---|---|
| `connected_accounts/twitch.py` | `autopilot/engine/twitch.py` |
| `publish/woopsocial.py` | `autopilot/engine/woopsocial.py` |
| `publish/multipart.py` | `autopilot/engine/multipart.py` |
| `publish/errors.py` | `autopilot/engine/errors.py` |
| `connected_accounts/models.py:AccountError` | `autopilot/engine/account.py` |
| `publish/uploadpost.py:PlatformOutcome,FanOutResult` | `autopilot/engine/results.py` |

Adapter changes include package-local imports and, in version 0.1.3, the documented Bluesky/LinkedIn Pages/WOOPTEST platform mappings, optional YouTube made-for-kids payload field, and WoopSocial post-validation endpoint. The standalone destination selection, approval snapshots, per-profile options and delivery tracking are maintained here. Standard dependencies include FastAPI, SQLite, FFmpeg, yt-dlp, Twitch and WoopSocial APIs. Provider accounts and permissions belong to the user.

The reusable gaming geometry, layout presets, framing and FFmpeg composition are also taken from `gaming/layout.py`, `gaming/layouts.json`, `gaming/framing.py` and `gaming/compose.py` at the same upstream snapshot. Imports use local adapters. The independent encoding adapter uses standard CPU H.264/AAC; no desktop configuration, editor, models, user media or credentials are copied.

`autopilot/feed.py` adapts the window-splitting algorithm developed for Clips Kitty's Twitch Clips addition on October 30, 2026.

The same upstream provider regression tests are reused under `tests/`, with local imports. The whole-clip compositor removes `-shortest` so short audio cannot truncate the video.

The full Gaming detector is restored from the same source snapshot: `gaming/detect.py` → `engine/detect.py`; selected tracking/detection/audio-crop primitives from `video/tracker.py` → `engine/tracker.py`; `video/capture.py` → `engine/capture.py`; and `video/asd.py` → `engine/asd.py`. Changes adapt package imports, CPU device/model paths, and reduce TalkNet's inference batch from 1,500 to 150 visual frames. The streamer-selection and webcam-border rules are retained, including the upstream regression tests. A basic Haar-only camera hint is no longer the standalone detector.

`autopilot/vendor/talknet/` retains the unmodified MIT TalkNet source and its license from the foundation's `third_party/talknet/`. It originates at [TaoRuijie/TalkNet-ASD](https://github.com/TaoRuijie/TalkNet-ASD). The adapter is `engine/asd.py`; the vendored README's references to the old adapter path describe the upstream layout. Runtime weights are not committed. The TalkNet mirror's published LFS SHA-256 matches the foundation's checkpoint; YOLOv8n pose retains the foundation's checkpoint and is verified by SHA-256 before loading. Ultralytics remains a third-party AGPL dependency. See `engine/models.py` for artifact hashes and download sources.
