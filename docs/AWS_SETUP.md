# Host Clips Kitty Autopilot on your own AWS server

This guide installs the independent Clips Kitty Autopilot app on Ubuntu in Amazon Lightsail. Your browser is the dashboard; the server keeps polling and processing when your computer is off. You do not need a separate Clips Kitty installation.

**BYOK:** use your own AWS account/server, Twitch app/viewer connection, WoopSocial API key and social profiles. All addresses in this walkthrough are examples or placeholders. There is no shared hosted account or project-funded usage. Whisper captions and Gaming models run on your server without an OpenAI API key. See [BYOK setup and privacy](BYOK.md).

Already installed? Go straight to [updates](#update-an-existing-installation) or [troubleshooting](#troubleshooting). Video/documentation-only updates do not require rebuilding your server.

## 1. Choose a server and review costs

Use your AWS account at the [Lightsail console](https://lightsail.aws.amazon.com/). Start with a **4 GB RAM, 2 vCPU, 80 GB disk, x86/AMD64 Ubuntu 24.04 LTS** instance with public IPv4. The full Gaming pipeline uses YOLOv8, TalkNet, OpenCV, local Whisper captions and FFmpeg. A GPU is not required. This is the configuration used for the project's cloud checks; 512 MB/1 GB plans are not the setup tested here. CPU processing can take several minutes per clip.

Check the current [Lightsail price](https://aws.amazon.com/lightsail/pricing/) before creating the instance. Hosting is separate from the free, open-source app. Review credits and expiration in AWS Billing. A budget notification is an alert, not a hard spending cap; see [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html). This app's installer does not configure AWS billing.

In Lightsail choose **Create instance**, select your region, **Linux/Unix**, then **OS Only → Ubuntu 24.04 LTS**, the appropriate IPv4 plan and a name such as `clips-kitty-autopilot`. Ohio is the region used for the project demonstration; choose a region suitable for your own users. Automatic snapshots are optional and have separate storage costs. See [AWS's instance creation instructions](https://docs.aws.amazon.com/lightsail/latest/userguide/getting-started-with-amazon-lightsail.html).

## 2. Attach a static public IP

Open Lightsail **Networking → Create static IP**, select the same region and attach it to this instance. Give the IP resource a name. Use the **public IPv4**, not the `172.x` private address shown in the terminal. A static address keeps the browser URL stable across stop/start operations. See [AWS's static-IP guide](https://docs.aws.amazon.com/lightsail/latest/userguide/lightsail-create-static-ip.html).

For the examples below, replace `203.0.113.10` with your actual static IPv4. That address is an example, not a running server.

## 3. Open the web firewall ports

In the instance's **Networking** tab, allow inbound IPv4:

| Application | Protocol | Port | Source |
|---|---|---|---|
| HTTP | TCP | 80 | Any IPv4 address |
| HTTPS | TCP | 443 | Any IPv4 address |
| SSH | TCP | 22 | Your IP, with Lightsail browser SSH enabled |

The SSH rule must retain at least one allowed source or the Lightsail browser SSH service. Do not remove your working SSH access. Ports 8000 and 8877 are internal and need no public rule. If you separately configure IPv6 DNS, configure corresponding web rules there too. See [AWS firewall instructions](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-editing-firewall-rules.html).

## 4. Install Docker on the new Ubuntu instance

Open the instance's **Connect using SSH** terminal. Run these commands on that server, not in your local Windows terminal. This block follows Docker's official apt-repository method on a fresh Ubuntu installation; if Docker is already installed, first check `sudo docker compose version` and skip installation when it works. For existing conflicting packages, follow [Docker's Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/) before continuing.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker compose version
```

Using `sudo` avoids needing to log out and back in to change Docker group membership.

## 5. Install the app and HTTPS

Choose a hostname pointing to your static IP. With your own domain, create a DNS A record pointing to the IP. Otherwise [sslip.io](https://sslip.io/) can provide an IP-based hostname: the example `203.0.113.10` becomes `203-0-113-10.sslip.io`.

In the server SSH terminal:

```bash
git clone https://github.com/ColinGPT9/clips-kitty-autopilot.git
cd clips-kitty-autopilot
```

Replace the example hostname below with yours before running:

```bash
sudo bash scripts/deploy-lightsail.sh 203-0-113-10.sslip.io
```

The first build downloads dependencies. Wait for **App containers started**. Caddy obtains the HTTPS certificate after DNS resolves and ports 80/443 are reachable. The installer creates `.env.cloud` privately, generates the app password and preserves it on future runs. The SQLite database, encrypted credentials, models and renders live in Docker's persistent `autopilot-data` volume. Run one app instance/worker against that data.

Check the public health route, using your hostname:

```bash
curl --fail --show-error https://203-0-113-10.sslip.io/health
```

Expect JSON identifying **Clips Kitty Autopilot**, its version and `"ok":true`. Certificate setup can take a minute. Do not bypass a certificate error to enter your password; see troubleshooting below.

## 6. Sign in

Open `https://YOUR-HOSTNAME` in a normal browser tab. Your username is **owner**, all lowercase. It is different from the Ubuntu SSH username.

Retrieve the app password privately in the server terminal:

```bash
cd ~/clips-kitty-autopilot
sudo grep '^AUTOPILOT_PASSWORD=' .env.cloud
```

Paste only the characters after `AUTOPILOT_PASSWORD=` into the login box. Keep this password and `.env.cloud` private. AWS account credentials are not used for the app login.

## 7. Connect Twitch and WoopSocial

1. In the app, open **Settings**. Save your Twitch application's public Client ID and choose **Connect Twitch**. The app uses Twitch's public-client device authorization flow, with no client secret. Enter the displayed code at Twitch's activation page and authorize your viewer account. Follow [Twitch's device-flow documentation](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#device-code-grant-flow) when registering your Twitch application. Public clip reads do not need broadcaster management permissions.
2. Connect the desired social profiles in your own WoopSocial account. In Clips Kitty Settings, save your WoopSocial API key, choose **Refresh connections**, and select the project if needed.
3. Check only the profiles you want to publish to and save. Connecting a profile does not automatically select it. Instagram alone is fine for an initial test; the app also supports the other documented WoopSocial networks. Pinterest requires a board ID; YouTube and TikTok expose visibility options. Apply any required TikTok brand disclosures.
4. Confirm the dashboard's destination list. Keep keys and tokens in Settings; they are encrypted in the data volume.

## 8. Preview your first whole clip

Add a Twitch channel, view target and lookback window. Leave **Ask first**, **Gaming** and **captions** enabled. Use media you are authorized to process.

**Check now** reads clips even while watching is paused. Clips already over the target on the first check appear under **Earlier clips**, unless backfill was explicitly enabled. Choose **Clip this** for an earlier clip you want to try. **Start watching** allows queued rendering and later scheduled polling. View counts are read from Twitch; they can lag.

The whole viewer clip becomes one vertical video, with no trimming or moment selection. First use downloads detector/caption models. Preview the finished result before publishing. In Ask First mode, do not press Schedule if you only want an unposted preview.

One **Schedule** approval creates a real provider post for the displayed selected profiles, without a second WoopSocial approval. The default limits are five clips per day and five upcoming clips, shared across watched channels; each selected profile receives that clip. Automatic mode is a separate opt-in. Damage Control opens a preview popup and sends no takedowns, deletion requests or attorney messages.

## Update an existing installation

You do not need a new server or reboot for an app update. In SSH, use the **same hostname** as the original deployment:

```bash
cd ~/clips-kitty-autopilot
git pull --ff-only
sudo bash scripts/deploy-lightsail.sh YOUR-EXISTING-HOSTNAME
```

Wait for the build to finish, check `/health`, then refresh the browser tab with **Ctrl + F5**. The installer preserves `.env.cloud` and Docker volumes. If it reports another saved hostname, review `.env.cloud` privately instead of deleting it. If `git pull` refuses local changes, inspect them rather than overwriting server configuration.

## Troubleshooting

From `~/clips-kitty-autopilot`, inspect containers and recent logs:

```bash
sudo docker compose --project-name clips-kitty-autopilot --env-file .env.cloud -f compose.cloud.yaml ps
sudo docker compose --project-name clips-kitty-autopilot --env-file .env.cloud -f compose.cloud.yaml logs --tail=80 autopilot https
df -h
free -h
```

| Symptom | What to check |
|---|---|
| Browser cannot reach the app | Correct public static IP, DNS hostname, inbound ports 80/443 and running containers. |
| HTTPS certificate pending | Wait briefly, verify the hostname resolves to the static IP, and check the `https` container logs. |
| Login fails | Username is `owner`; use the value after `AUTOPILOT_PASSWORD=`, without the key name or extra spaces. |
| Old UI after an update | Verify `/health` shows the expected release, then use Ctrl + F5. |
| No queued rendering | Start watching; Pause leaves work queued. Ensure the clip was queued rather than left under Earlier clips. |
| Rendering takes several minutes | Expected on CPU, especially first model download. Verify disk/memory and processing logs before restarting. |
| No publish | Ask First needs explicit approval; check selected profiles, available schedule slots and provider validation/errors. |
| Check WoopSocial / partial failure | Inspect the provider dashboard and per-profile results. The app holds ambiguous sends instead of automatically sending duplicates. |

Keep `.env.cloud`, `encryption.key` and any log lines containing credentials or temporary media URLs out of public issues. Back up the full application data volume, including `encryption.key`, and the private deployment configuration before replacing the instance. Losing the encryption key requires reconnecting accounts.

When you stop using the server, review AWS resources and billing. [Stopping an instance does not end its instance charges](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-frequently-asked-questions-faq-billing-and-account-management.html). Back up needed data before deleting resources; separately review snapshots, disks and unattached static IPs.
