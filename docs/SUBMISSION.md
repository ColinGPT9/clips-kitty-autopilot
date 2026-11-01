# Submission handoff: Clips Kitty Autopilot

Repository: https://github.com/ColinGPT9/clips-kitty-autopilot

Starter foundation: https://github.com/ColinGPT9/clips-studio

Deployment: https://13-184-154-246.sslip.io (owner authentication required). Hosted on AWS Lightsail in Ohio; see [actual cloud checks and remaining evidence](LIVE_TEST.md). Provide judge access privately rather than committing credentials.

## Description draft

Clips Kitty Autopilot lets a Twitch community choose the highlights. It watches viewer-made Twitch clips until they reach a creator's view target, turns the entire clip into a vertical Gaming video with optional local captions, credits the viewer, and schedules it to explicitly selected social profiles through WoopSocial. The app supports all documented WoopSocial networks; Instagram alone was selected for the owner's live test. The owner can approve each clip or explicitly enable automatic scheduling. A shared five-clip daily budget, five-upcoming limit, duplicate/overlap filtering and persistent restart recovery keep a busy channel manageable.

This independent browser app has its own dashboard, data store, worker and container setup. It uses the pre-existing open-source Clips Kitty application as a disclosed starter foundation for provider adapters and Gaming rendering. Twitch Autopilot work was developed October 30-31; standalone assembly is November 1, 2026. Exact reused files and source revision are in PROVENANCE.md. A new repository does not establish eligibility by itself; do not describe reused code as newly authored or imply organizer approval.

Codex implemented the standalone application, adapted library imports, wrote regression tests and packaging, and ran validation. The active build thread's session ID, read from `CODEX_THREAD_ID`, is `01a18b17-1906-7f23-b4c4-9a99fd010bd9`. Confirm the displayed thread with Codex `/status` when submitting.

## Complete before submitting

- Review the official [rules](https://twitchcon-codex.devpost.com/rules), including the new-project requirement and organizer clarification supplied by the entrant. The organizers determine eligibility.
- Latest source checks passed on Windows, Linux and the CPU container; follow README setup to test this repository independently.
- Real Twitch reads and a corrected whole Gaming output ran in this app. Actual cloud dashboard and preview footage were captured for the new demo. Do not reuse desktop footage as if it were this app.
- The latest review video, `Clips-Kitty-Contest-Demo-WoW-Forever.mp4`, is **133.420 seconds**. A wedding-regret hook pays off in the anonymous Damage Control segment later. WoW: Forever footage leads the holiday-gaming section, which also names Zelda and GTA and explains that the workflow is built for whatever game is streamed. Actual saved threshold edits demonstrate targets of 100 and 10,000 views for smaller and larger communities; the original target was restored. The WoW edit and owner's Instagram recording are labeled as a **previously published example**, without claiming a new cloud delivery. The version 0.1.2 clip controls and actual Codex build excerpts remain visible. The WoopSocial section names its supported networks and explains explicit profile selection, with Instagram used only as the example. The closing promotes Clips Kitty across socials. Preferred female narration, audio normalization, visual checks and full-file decoding passed.
- Upload the review video publicly to YouTube; the owner performs this step. Only include third-party material/trademarks with required permissions. Enter the actual public URL in Devpost; no demo URL is supplied here yet.
- State the actual hosting platform: AWS Lightsail, with persistent Docker volumes and Caddy HTTPS. The optional Render Blueprint was not deployed.

The provided deadline is November 2, 2026; the prior rules check recorded 2 p.m. Pacific / 5 p.m. Eastern. Verify the form's current deadline when submitting.
