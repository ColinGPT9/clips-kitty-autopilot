# Validation

Standalone application assembled November 1, 2026. Automated checks use synthetic clip observations and offline providers. They are not evidence that a real Twitch clip crossed a target in this new app or that this new app sent a public post.

Local results: Ruff passed; **174 pytest checks passed**, including three real FFmpeg render/decode cases; the Windows-compatible subset passed **171 checks**. JavaScript syntax and the hidden Chromium browser regression passed. A distribution wheel built successfully. The independent server started on localhost:8877 and its health endpoint returned version 0.1.0.

Local checks cover baseline versus later crossing, backfill, duplicate suppression across restart, same-VOD overlap, five-upcoming admission, shared five-per-day DST-aware scheduling, owner authentication, CSRF protection, secret redaction/encryption, explicit account selection and ambiguous-send recovery. Real FFmpeg checks render/decode 1080×1920 whole clips with no audio, short audio, and a separate facecam. The hidden-browser regression checks the actual HTML/CSS/JavaScript at desktop and mobile widths, safe title rendering, no writes on mount, the visible destination, one-click scheduling and request-free satire. It uses clearly synthetic fixtures.

The reused Twitch and WoopSocial SDK regression suites are retained with local package imports. Their scenarios include permission/row validation, pagination, rate limits, safe errors and provider payloads. Provider fakes never call the live services.

Pending live checks: connect the new app's Twitch account; verify a real read and whole render in its own UI; explicitly approve any public Instagram test; verify provider delivery. No new public post or new target crossing has been fabricated. Cloud deployment and fresh demonstration video remain separate tasks. Existing desktop-app evidence is historical context for the reused foundation, not this standalone deployment.

GitHub [run 41279148805](https://github.com/ColinGPT9/clips-kitty-autopilot/actions/runs/41279148805) passed all three jobs on source commit `e66d07d`: Linux tests/browser/render checks, Windows tests, and Docker build with independent container startup/authentication checks. Local Docker is unavailable on the development machine; the container was validated in GitHub CI. The prepared Render Blueprint also passed validation against Render's published JSON schema.
