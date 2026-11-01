# Validation

Standalone application assembled November 1, 2026. Automated checks use synthetic clip observations and offline providers. They are not evidence that a real Twitch clip crossed a target in this new app or that this new app sent a public post.

Local results: Ruff passed; **174 pytest checks passed**, including three real FFmpeg render/decode cases; the Windows-compatible subset passed **171 checks**. JavaScript syntax and the hidden Chromium browser regression passed. A distribution wheel built successfully. The independent server started on localhost:8877 and its health endpoint returned version 0.1.0.

Local checks cover baseline versus later crossing, backfill, duplicate suppression across restart, same-VOD overlap, five-upcoming admission, shared five-per-day DST-aware scheduling, owner authentication, CSRF protection, secret redaction/encryption, explicit account selection and ambiguous-send recovery. Real FFmpeg checks render/decode 1080×1920 whole clips with no audio, short audio, and a separate facecam. The hidden-browser regression checks the actual HTML/CSS/JavaScript at desktop and mobile widths, safe title rendering, no writes on mount, the visible destination, one-click scheduling and request-free satire. It uses clearly synthetic fixtures.

The reused Twitch and WoopSocial SDK regression suites are retained with local package imports. Their scenarios include permission/row validation, pagination, rate limits, safe errors and provider payloads. Provider fakes never call the live services.

Pending live checks: connect the new app's Twitch account; verify a real read and whole render in its own UI; explicitly approve any public Instagram test; verify provider delivery. No new public post or new target crossing has been fabricated. Cloud deployment and fresh demonstration video remain separate tasks. Existing desktop-app evidence is historical context for the reused foundation, not this standalone deployment.

GitHub [run 41279148805](https://github.com/ColinGPT9/clips-kitty-autopilot/actions/runs/41279148805) passed all three jobs on source commit `e66d07d`: Linux tests/browser/render checks, Windows tests, and Docker build with independent container startup/authentication checks. Local Docker is unavailable on the development machine; the container was validated in GitHub CI. The prepared Render Blueprint also passed validation against Render's published JSON schema.

## Full Gaming detector restoration

After restoring YOLOv8n-pose/TalkNet and retaining Whisper captions, local regression results are **199 passed**, including 25 additional detector/adapter regressions; the Windows-compatible subset passed **196 checks**. Real CPU YOLO and TalkNet inference also passed a synthetic 151-frame smoke check, independently of the offline mocks.

A private, previously authorized 60.015-second Twitch source was processed by the new standalone model subprocesses and FFmpeg: output 60.100 seconds, 1080×1920, audio retained, Whisper captions written. That clip did not produce a confident overlay-camera selection, so output used the whole-source fit layout; it is not evidence of a successful automatic split on that clip. The run took 214.61 seconds on the development Windows machine and the maximum sampled process-tree RSS was 955.4 MiB. This is one local measurement, not a Lightsail benchmark or an upper bound for other media. The source/output remain private runtime files and were not posted publicly or used as a new target-crossing observation.

CI now additionally validates the cloud Compose/Caddy configuration, builds CPU-only PyTorch, and runs real YOLO/TalkNet inference plus speech-caption generation under a 3 GiB container limit. Those new CI results must be checked on the restored source revision before deployment is called verified.
