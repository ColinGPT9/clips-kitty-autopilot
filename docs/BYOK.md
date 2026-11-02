# BYOK: your keys, accounts and hosting

Clips Kitty Autopilot is self-hosted. Each installer supplies their own connections and pays for any usage on those accounts. Cloning the repository does not grant access to the project creator's server, social accounts, API keys, credits or Codex subscription.

| Part | What you supply | Where usage runs |
|---|---|---|
| Twitch | Your own Twitch application Client ID and viewer account authorization | Twitch API requests use your connected authorization/application |
| WoopSocial | Your own API key, project and connected social profiles | Uploads and publishing use your WoopSocial account's allowances |
| Hosting | Your own computer, or a server in your own AWS/other hosting account | Compute, storage and hosting costs belong to your installation |
| Captions and Gaming layout | Your installation downloads the local models on first use | Whisper, YOLOv8, TalkNet, OpenCV and FFmpeg run on your computer/server; no OpenAI API key is required |
| Dashboard login | Your own configured or installation-generated password | The generic username `owner` signs in to your installation only |

Codex was used to build the project. Running the app does not call Codex or consume the creator's Codex allowance. The current caption/render workflow does not call a hosted OpenAI inference service.

## Set up your installation

1. Follow the [README](../README.md) locally or the [AWS guide](AWS_SETUP.md) on your own server. Replace example hostnames/IPs with yours. `127.0.0.1` means your own computer, and `203.0.113.10` is documentation-only sample data.
2. Create your own app password. Each cloud installation generates a new password in its private `.env.cloud`; the repository includes no working password.
3. In Settings, save your own Twitch application's public Client ID and complete Twitch authorization with your own viewer account. No Twitch client secret is needed for this device flow.
4. Save your own WoopSocial key, refresh your connections, and check the social profiles you want. Fresh installations have no provider keys, project, selected social profiles or Twitch account. Ask First is the default, and automatic processing starts paused.
5. Preview a clip before scheduling. Publishing and its provider limits belong to the accounts you connected. Automatic mode is an explicit opt-in.

## Keep installation data private

`.env`, `.env.cloud` and the default `data/` directory (including its encryption key, database and connection state) are excluded from Git and from the Docker build context. The ignore files also exclude `backups/`, `.aws/`, and common private-key/database file extensions. Keep backups in a private location; these rules do not recognize every possible file name. Do not copy someone else's data volume or configuration into your server: reconnect using your own accounts instead.

Keys/tokens are encrypted in the installation's data volume. Keep the volume's `encryption.key` with your private backups so saved connections remain recoverable. Provider keys are entered in Settings and are not returned in the dashboard's public settings fields. Your hosting administrator still controls the machine and its storage.

The README and AWS walkthrough contain no private demo endpoint or shared credentials. Public source/provenance links identify this project and its upstream foundation; they do not grant access to anyone's provider quota. The demonstration video is an example of the workflow, not a public hosted service.
