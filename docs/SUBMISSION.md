# Submission handoff: Clips Kitty Autopilot

Copy-and-paste form answers: [Devpost submission fields](DEVPOST.md). Testing instructions: [Judge setup](JUDGE_SETUP.md).

Repository: https://github.com/ColinGPT9/clips-kitty-autopilot

Demo URL supplied by the entrant: https://youtu.be/_9trPSK_6gE. Confirm Public visibility and playback while signed out; the uploaded page could not be independently fetched during preparation.

Starter foundation: https://github.com/ColinGPT9/clips-studio

Deployment model: self-hosted, BYOK. Follow the [AWS setup guide](AWS_SETUP.md) using your own server and provider accounts. The private demonstration instance is not a public service or a source of shared usage; its address and login are not included here. See [actual cloud checks and remaining evidence](LIVE_TEST.md).

## Description draft

Clips Kitty Autopilot lets a Twitch community choose the highlights. It watches viewer-made Twitch clips until they reach a creator's view target, turns the entire clip into a vertical Gaming video with optional local captions, credits the viewer, and schedules it to explicitly selected social profiles through WoopSocial. The app supports all documented WoopSocial networks; Instagram alone was selected for the owner's live test. The owner can approve each clip or explicitly enable automatic scheduling. A shared five-clip daily budget, five-upcoming limit, duplicate/overlap filtering and persistent restart recovery keep a busy channel manageable.

This independent browser app has its own dashboard, data store, worker and container setup. It uses the pre-existing open-source Clips Kitty application as a disclosed starter foundation for provider adapters and Gaming rendering. Twitch Autopilot work was developed October 30-31; standalone assembly is November 1, 2026. Exact reused files and source revision are in PROVENANCE.md. A new repository does not establish eligibility by itself; do not describe reused code as newly authored or imply organizer approval.

Codex implemented the standalone application, adapted library imports, wrote regression tests and packaging, and ran validation. The active build thread's session ID, read from `CODEX_THREAD_ID`, is `01a18b17-1906-7f23-b4c4-9a99fd010bd9`. Confirm the displayed thread with Codex `/status` when submitting.

## Complete before submitting

- Review the official [rules](https://twitchcon-codex.devpost.com/rules), including the new-project requirement and organizer clarification supplied by the entrant. The organizers determine eligibility.
- Latest source checks passed on Windows, Linux and the CPU container; follow README setup to test this repository independently.
- Real Twitch reads and a corrected whole Gaming output ran in this app. Actual cloud dashboard and preview footage were captured for the new demo. Do not reuse desktop footage as if it were this app.
- The latest review video, `Clips-Kitty-Contest-Demo-WoW-Forever.mp4`, is **167.954 seconds**. A wedding-regret hook pays off in the anonymous Damage Control segment later. World of Warcraft: Forever footage leads the holiday-gaming section, which also names The Legend of Zelda: Ocarina of Time and Grand Theft Auto 6 and explains that the workflow is built for whatever game is streamed. Actual saved threshold edits demonstrate targets of 100 and 10,000 views for smaller and larger communities; the original target was restored. The WoW edit and owner's Instagram recording are labeled as a **previously published example**, without claiming a new cloud delivery. The version 0.1.2 clip controls and actual Codex build excerpts remain visible. The slower narration explains YOLOv8n person detection, TalkNet active-speaker matching, OpenCV camera-border refinement and Whisper speech captions. The publishing section explains Automatic posting after a view threshold, manual Ask First review, and WoopSocial as the service that publishes scheduled videos to connected social profiles; Instagram is the example. The closing promotes Clips Kitty across socials and points to the AWS setup guide linked from the GitHub README. D M C A is spoken as separate letters, and the preview notice adds that no lawyer was contacted. Preferred female narration, audio normalization, visual checks and full-file decoding passed.
- Enter the supplied YouTube URL in Devpost and verify Public visibility and sound. Only include third-party material/trademarks with required permissions.
- State the actual hosting platform: AWS Lightsail, with persistent Docker volumes and Caddy HTTPS. The optional Render Blueprint was not deployed.

The [official rules](https://twitchcon-codex.devpost.com/rules), checked November 1, give the deadline as **November 2, 2026, 2 p.m. Pacific / 5 p.m. Eastern**. A saved draft is not submitted; finish Devpost's final submission step and verify its Submitted confirmation.
