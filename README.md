# Clips Kitty Autopilot

A standalone, self-hosted web app for the moments a Twitch community already chose. Watch a channel's viewer-made clips, set a view target, preserve the whole clip in a vertical Gaming layout, review it and schedule it to your selected social profiles through WoopSocial. Every post credits the viewer who clipped it.

**Used as starter template / foundation:** [Clips Kitty](https://github.com/ColinGPT9/clips-studio), a pre-existing AGPL application, provides reusable Twitch/WoopSocial adapters and the Gaming renderer. This is a separate repository and runnable application with its own dashboard, database and worker. See [source provenance](PROVENANCE.md) for reused code and dates; the source app is not represented as newly created here.

## What it does

- Checks Twitch every 15 minutes. Clips below the chosen view target are checked again later.
- First-look clips already above the target stay under **Earlier clips**, unless backfill is explicitly enabled. Later crossings are recorded separately.
- Downloads and renders the **entire** viewer clip, up to three minutes, as 1080×1920 H.264/AAC. YOLOv8n pose locates people, TalkNet identifies the speaking streamer and OpenCV refines the facecam region. With a facecam, the game panel uses the foundation's webcam-aware crop so the streamer is shown once. Without a facecam, the whole source frame is fitted. Local Whisper captions are enabled by default. A silent game character or full-screen speaker does not automatically become a split-screen facecam.
- Defaults to **five clips per day and five upcoming clips**, shared across channels, at least one hour apart. Each clip uses one slot and goes to each selected profile. Additional clips wait for room. Same IDs and strongly overlapping moments from the same VOD are suppressed.
- **Ask first** is the default. One **Schedule to @account** click schedules directly through WoopSocial; a second provider-side approval is not part of this flow. Automatic mode is an explicit opt-in.
- Shows the exact selected destinations. Supports WoopSocial's Instagram, TikTok, YouTube, Facebook, X, Threads, LinkedIn, LinkedIn Pages, Pinterest and Bluesky profiles, plus WOOPTEST sandbox accounts. Profiles are individually selected; connecting or refreshing an account never selects it automatically. Approval freezes the profiles and their options, so changing Settings cannot redirect approved work. Status and links are tracked separately for each profile; partial failures are held for inspection without resending successful posts.
- Remembers work after restarts. Ambiguous sends are held for inspection instead of retried into duplicate posts. This is not a guarantee of exactly-once behavior by third-party systems.
- Ready clips show **Schedule → Damage Control → Deny**. Damage Control opens the satirical preview without deleting anything, contacting anyone or sending takedowns.

## Run locally

Requires Python 3.11+, [FFmpeg/FFprobe](https://ffmpeg.org/download.html) on PATH, and a browser. Install the media dependencies for Whisper captions, TalkNet, YOLOv8 and OpenCV. No existing Clips Kitty checkout or desktop app is needed. The Docker image installs CPU-only PyTorch; local pip installs follow the PyTorch distribution selected for your environment.

PowerShell:

```powershell
git clone https://github.com/ColinGPT9/clips-kitty-autopilot.git
cd clips-kitty-autopilot
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev,media]'
Copy-Item .env.example .env
# Edit .env and set AUTOPILOT_PASSWORD to your own password (12+ characters).
.\.venv\Scripts\python.exe -m autopilot
```

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,media]'
cp .env.example .env
# Set AUTOPILOT_PASSWORD in .env, then:
.venv/bin/python -m autopilot
```

Open **http://127.0.0.1:8877**, username **owner**, using your configured password. If no password is set, the app generates one in `data/owner-password.txt`. Environment variables override `.env`. Use `FFMPEG_BINARY` / `FFPROBE_BINARY` for explicit executable paths.

## Connect and try it

1. In Settings, save your Twitch application's public Client ID and click **Connect Twitch**. Enter the displayed code at Twitch's activation page. Use a **Public** Twitch application supporting device authorization; no client secret is used. See [Twitch device-flow documentation](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#device-code-grant-flow). A viewer account can read public clips; broadcaster management scopes are not requested.
2. Save your WoopSocial API key, refresh connections, choose a project if needed, check the exact profiles you want and save. Connect missing profiles in WoopSocial first. Select a board for Pinterest, visibility for YouTube/TikTok, and any applicable TikTok brand disclosures. Credentials stay in Settings and encrypted local storage. Existing Instagram-only settings migrate with only that profile selected.
3. Add a Twitch channel and view target. Leave **Ask first** selected for the initial test. **Check now** reads Twitch while watching is paused; queued rendering begins after **Start watching**. It does not publish merely because a card is displayed.
4. Preview a completed whole clip and its destination list, then click **Schedule** to schedule it to those profiles. One approval sends it without another approval in WoopSocial. The provider validates each network's requirements before a post is created. Scheduling uses the next free local slot, at least 17 minutes ahead. The saved time and each profile's delivery status appear under Schedule.
5. Leave the server running. Pause stops new polling/rendering and automatic approvals; an explicit approval already given still proceeds, and scheduled provider posts remain scheduled. To cancel a provider post, use WoopSocial.

The daily budget covers clips reserved by **this app**; a clip sent to several profiles counts once toward the five-clip limit and once per selected profile's provider allowance. Existing posts created by other tools are not imported. WoopSocial and each network's limits still apply. Only use media and integrations you are authorized to use. Twitch view counts can lag.

## Container and cloud

```bash
docker compose up --build -d
```

Set `AUTOPILOT_PASSWORD` in `.env` first. Compose binds localhost:8877 and retains its SQLite database, encrypted credentials, media and models in a named volume. Run **one instance / one worker** on a persistent disk. Start testing the full Gaming pipeline on a **4 GB RAM CPU server**. This is a deployment starting point, not a benchmarked Lightsail guarantee. Camera detection, Whisper transcription and FFmpeg encoding run sequentially; detector/caption models run in separate short-lived processes so their memory is released before the next stage. TalkNet inference uses bounded 150-frame batches. Do not use ephemeral serverless hosting for the FFmpeg worker. Models download on first use; CPU processing can take several minutes per clip. YOLO/TalkNet downloads are checked against pinned SHA-256 hashes and saved on the data volume.

[`render.yaml`](render.yaml) is an optional Docker Blueprint with a persistent disk and generated owner password. Review the selected paid plan and disk before deploying; no cloud service is provisioned by cloning this repository. Retrieve the generated `AUTOPILOT_PASSWORD` from your host's environment settings and use HTTPS. Details: [Render Blueprint reference](https://render.com/docs/blueprint-spec). Actual hosting and provider connection checks are recorded in [validation](docs/VALIDATION.md).

For an Ubuntu Lightsail server with Docker, the HTTPS deployment is:

```bash
git clone https://github.com/ColinGPT9/clips-kitty-autopilot.git
cd clips-kitty-autopilot
sudo bash scripts/deploy-lightsail.sh your.public.hostname
```

Attach a static IPv4 address, point your hostname at it, and allow TCP ports 80/443 in Lightsail. If you have no domain, a hostname like `YOUR-IP-WITH-DASHES.sslip.io` can resolve to your public IP; see [sslip.io](https://sslip.io/) for the service and certificate limits. [`compose.cloud.yaml`](compose.cloud.yaml) runs Caddy for automatic HTTPS and retains certificates and application data in Docker volumes. Only the proxy exposes public ports; the Python service stays on Docker's internal network. The installer generates a private owner password in `.env.cloud` and preserves it on subsequent runs. View it privately on the server when signing in. This script configures the app; it does not modify AWS billing, account plans, firewall rules or purchase cloud resources.

Back up the entire data volume, including `encryption.key`. If you supply `AUTOPILOT_ENCRYPTION_KEY`, retain that same Fernet key across deployments. Losing the key requires reconnecting accounts. Media retention is manual; pause and remove unused completed download/render files when disk space is low, keeping the database for deduplication history.

## Development and submission

```bash
python -m ruff check .
python -m pytest
node --check autopilot/static/app.js
```

Tests use synthetic fixtures and offline provider fakes. Tests marked `media` use real FFmpeg rendering and full decoding. CI checks Windows/Linux and independent container startup. No automated test sends a live social post.

- [Architecture and API](docs/ARCHITECTURE.md)
- [Validation and limitations](docs/VALIDATION.md)
- [Submission handoff](docs/SUBMISSION.md)
- [Provenance](PROVENANCE.md)

Licensed under [GNU AGPL v3](LICENSE). This project uses Twitch and WoopSocial APIs and is not endorsed by those services.
