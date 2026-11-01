# Clips Kitty Autopilot

A standalone, self-hosted web app for the moments a Twitch community already chose. Watch a channel's viewer-made clips, set a view target, preserve the whole clip in a vertical Gaming layout, review it and schedule an Instagram Reel through WoopSocial. Every post credits the viewer who clipped it.

**Used as starter template / foundation:** [Clips Kitty](https://github.com/ColinGPT9/clips-studio), a pre-existing AGPL application, provides reusable Twitch/WoopSocial adapters and the Gaming renderer. This is a separate repository and runnable application with its own dashboard, database and worker. See [source provenance](PROVENANCE.md) for reused code and dates; the source app is not represented as newly created here.

## What it does

- Checks Twitch every 15 minutes. Clips below the chosen view target are checked again later.
- First-look clips already above the target stay under **Earlier clips**, unless backfill is explicitly enabled. Later crossings are recorded separately.
- Downloads and renders the **entire** viewer clip, up to three minutes, as 1080×1920 H.264/AAC. Gameplay is fitted whole; an optional detected facecam gets a separate region. Local Whisper captions are enabled by default.
- Defaults to **five posts per day and five upcoming clips**, shared across channels, at least one hour apart. Additional clips wait for room. Same IDs and strongly overlapping moments from the same VOD are suppressed.
- **Ask first** is the default. One **Schedule to @account** click schedules directly through WoopSocial; a second provider-side approval is not part of this flow. Automatic mode is an explicit opt-in.
- Shows the exact selected Instagram destination. Approval freezes that destination; changing Settings cannot silently redirect an approved clip. No YouTube or TikTok destination is exposed.
- Remembers work after restarts. Ambiguous sends are held for inspection instead of retried into duplicate posts. This is not a guarantee of exactly-once behavior by third-party systems.
- Includes a generic **Damage Control** satire popup. It does not delete anything, contact anyone or send takedowns.

## Run locally

Requires Python 3.11+, [FFmpeg/FFprobe](https://ffmpeg.org/download.html) on PATH, and a browser. Install the optional media dependencies for captions and face detection. No existing Clips Kitty checkout or desktop app is needed.

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
2. Save your WoopSocial API key, refresh connections, choose a project if needed, select the exact Instagram account and save. Connect the profile in WoopSocial first if it is absent. Credentials stay in Settings and encrypted local storage.
3. Add a Twitch channel and view target. Leave **Ask first** selected for the initial test. **Check now** reads Twitch while watching is paused; queued rendering begins after **Start watching**. It does not publish merely because a card is displayed.
4. Preview a completed whole clip, then click **Schedule to @youraccount** if you want a real public Reel scheduled. Approval sends it without another approval in WoopSocial. Scheduling uses the next free local slot, at least 17 minutes ahead. The actual saved time appears under Schedule.
5. Leave the server running. Pause stops new polling/rendering and automatic approvals; an explicit approval already given still proceeds, and scheduled provider posts remain scheduled. To cancel a provider post, use WoopSocial.

The daily budget covers posts reserved by **this app**. Existing posts created by other tools are not imported. WoopSocial and Instagram limits still apply. Only use media and integrations you are authorized to use. Twitch view counts can lag.

## Container and cloud

```bash
docker compose up --build -d
```

Set `AUTOPILOT_PASSWORD` in `.env` first. Compose binds localhost:8877 and retains its SQLite database, encrypted credentials, media and models in a named volume. Run **one instance / one worker** on a persistent disk. Do not use ephemeral serverless hosting for the FFmpeg worker. Caption models download on first use; CPU transcription/rendering can take several minutes.

[`render.yaml`](render.yaml) is an optional Docker Blueprint with a persistent disk and generated owner password. Review the selected paid plan and disk before deploying; no cloud service is provisioned by cloning this repository. Retrieve the generated `AUTOPILOT_PASSWORD` from your host's environment settings and use HTTPS. Details: [Render Blueprint reference](https://render.com/docs/blueprint-spec). Actual hosting and provider connection checks are recorded in [validation](docs/VALIDATION.md).

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
