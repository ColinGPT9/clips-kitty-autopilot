# Validation

Standalone application assembled November 1, 2026. Automated checks use synthetic clip observations and offline providers. They are not evidence that a real Twitch clip crossed a target in this new app or that this new app sent a public post.

Local results: Ruff passed; **174 pytest checks passed**, including three real FFmpeg render/decode cases; the Windows-compatible subset passed **171 checks**. JavaScript syntax and the hidden Chromium browser regression passed. A distribution wheel built successfully. The independent server started on localhost:8877 and its health endpoint returned version 0.1.0.

Local checks cover baseline versus later crossing, backfill, duplicate suppression across restart, same-VOD overlap, five-upcoming admission, shared five-per-day DST-aware scheduling, owner authentication, CSRF protection, secret redaction/encryption, explicit account selection and ambiguous-send recovery. Real FFmpeg checks render/decode 1080×1920 whole clips with no audio, short audio, and a separate facecam. The hidden-browser regression checks the actual HTML/CSS/JavaScript at desktop and mobile widths, safe title rendering, no writes on mount, the visible destination, one-click scheduling and request-free satire. It uses clearly synthetic fixtures.

The reused Twitch and WoopSocial SDK regression suites are retained with local package imports. Their scenarios include permission/row validation, pagination, rate limits, safe errors and provider payloads. Provider fakes never call the live services.

Live deployment, account connections, real Twitch reads on two channels, whole Gaming rendering, webcam-aware cropping and corrected caption placement have now been checked in the standalone app; see [cloud test evidence](LIVE_TEST.md). The owner kept the new test clips unposted, so public Instagram delivery is not claimed. A new natural target crossing and the final public demonstration URL remain unverified. Existing desktop-app evidence is historical context for the reused foundation, not this standalone deployment.

GitHub [run 41279148805](https://github.com/ColinGPT9/clips-kitty-autopilot/actions/runs/41279148805) passed all three jobs on source commit `e66d07d`: Linux tests/browser/render checks, Windows tests, and Docker build with independent container startup/authentication checks. Local Docker is unavailable on the development machine; the container was validated in GitHub CI. The prepared Render Blueprint also passed validation against Render's published JSON schema.

## Full Gaming detector restoration

After restoring YOLOv8n-pose/TalkNet and retaining Whisper captions, local regression results are **199 passed**, including 25 additional detector/adapter regressions; the Windows-compatible subset passed **196 checks**. Real CPU YOLO and TalkNet inference also passed a synthetic 151-frame smoke check, independently of the offline mocks.

A private, previously authorized 60.015-second Twitch source was processed by the new standalone model subprocesses and FFmpeg: output 60.100 seconds, 1080×1920, audio retained, Whisper captions written. That clip did not produce a confident overlay-camera selection, so output used the whole-source fit layout; it is not evidence of a successful automatic split on that clip. The run took 214.61 seconds on the development Windows machine and the maximum sampled process-tree RSS was 955.4 MiB. This is one local measurement, not a Lightsail benchmark or an upper bound for other media. The source/output remain private runtime files and were not posted publicly or used as a new target-crossing observation.

CI additionally validates the cloud Compose/Caddy configuration, builds CPU-only PyTorch, and runs real YOLO/TalkNet inference plus speech-caption generation under a 3 GiB container limit. [Run 41284049543](https://github.com/ColinGPT9/clips-kitty-autopilot/actions/runs/41284049543) passed after adding the clean-container SciPy dependency.

## Caption placement correction

The first real cloud Gaming render exposed overlapping captions where the Twitch source already contained subtitles. The correction positions generated captions above the gameplay divider for split layouts and keeps the existing bottom margin for the whole-source fit layout. Two regression cases cover those placements.

Local results on source revision `810d23e`: **201 passed**, Ruff passed, and the platform subset passed **198 checks** (three real-media cases deselected). [Run 41288528752](https://github.com/ColinGPT9/clips-kitty-autopilot/actions/runs/41288528752) passed all three jobs: Linux tests/browser/render/wheel checks, Windows tests/wheel checks, and independent container startup plus real model inference. The container's synthetic 151-frame YOLO/TalkNet smoke check reported 852.6 MiB peak RSS; real Whisper speech-caption generation also passed within the same 3 GiB limit. These fixtures verify execution and resource fit for those inputs; they are not Twitch view-count or posting evidence.

The owner updated the running Lightsail image and confirmed the caption helper import. That whole-clip cloud rerender completed in about 9 minutes 57 seconds and passed full decoding and visual caption checks at four timestamps. At that stage the health version remained `0.1.0`; the subsequent framing release uses `0.1.1` for independent deployment verification.

## Webcam-aware game crop

Version **0.1.1** restores the foundation's automatic game crop beside a detected webcam, rather than forcing the whole source into the game band. The no-camera whole-source fit is unchanged. A failing-first real FFmpeg test reproduces the duplicate source-webcam defect and verifies its absence in decoded output after the correction. Local checks pass **202 tests**, including four real-media cases, and the platform subset passes **198**. [Run 41292553292](https://github.com/ColinGPT9/clips-kitty-autopilot/actions/runs/41292553292) passed Linux, Windows and the real-model 3 GiB CPU container checks on `2ed3bca`.

The live health endpoint now reports **0.1.1**. A fresh cloud pass completed in about **11 minutes 47 seconds**, and the full 60.100-second video passed decoding and four visual checks: game crop excludes the source webcam, the streamer appears once, and captions stay above gameplay. Actual preview footage and the corrected output were used to rebuild the **125.581-second** review demo with the requested local female voice. Final audio and full-file decoding passed. The private LIRIK test also passed feed filtering, edited-target admission, repeated-poll deduplication and a 15.900-second no-camera render; it is not claimed as a natural view-count crossing or a public post.

## Clip actions: version 0.1.2

Ready clips now show **Schedule → Damage Control → Deny**. The popup uses a normal Damage Control label with a concise preview capability note. A failing-first browser regression verified the three controls' order, opening the same dialog from the clip card, no reads or writes caused by opening it, and one-click scheduling behavior. The desktop/mobile browser checks, JavaScript syntax, Ruff, **202 pytest checks** and **198 platform checks** passed locally. [Run 41295639357](https://github.com/ColinGPT9/clips-kitty-autopilot/actions/runs/41295639357) passed all three jobs on `7ee7ecd`.

The deployed health endpoint reports **0.1.2**. Actual authenticated browser captures verify the new action order and popup, including opening Damage Control from the Asmongold clip card. The updated **143.834-second** demo contains those captures, the requested holiday-gaming introduction, the corrected cloud render and the owner's 14.328-second Instagram screen recording. The desktop publishing example is labeled separately from the unposted cloud clip. The preferred local female voice, normalized audio and full-file decoding passed verification; visual spot checks cover the introduction, actions, published example and revised popup segment.
