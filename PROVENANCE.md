# Source provenance

Starter foundation: [Clips Kitty](https://github.com/ColinGPT9/clips-studio), a pre-existing open-source application. This independent repository reuses its provider adapters and result/error contracts as a library. It is not a GitHub fork.

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

Adapter changes are limited to package-local imports. Standalone server, storage, dashboard and worker are maintained in this repository. Standard dependencies include FastAPI, SQLite, FFmpeg, yt-dlp, Twitch and WoopSocial APIs. Provider accounts and permissions belong to the user.

The reusable gaming geometry, layout presets, framing and FFmpeg composition are also taken from `gaming/layout.py`, `gaming/layouts.json`, `gaming/framing.py` and `gaming/compose.py` at the same upstream snapshot. Imports use local adapters. The independent encoding adapter uses standard CPU H.264/AAC; no desktop configuration, editor, models, user media or credentials are copied.

`autopilot/feed.py` adapts the window-splitting algorithm developed for Clips Kitty's Twitch Clips addition on October 30, 2026.

The same upstream provider regression tests are reused under `tests/`, with local imports. The whole-clip compositor removes `-shortest` so short audio cannot truncate the video.
