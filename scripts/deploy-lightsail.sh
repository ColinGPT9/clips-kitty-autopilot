#!/usr/bin/env bash
# Run inside the repository on an Ubuntu Lightsail server with Docker installed.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
domain="${1:-}"
if [[ ! "$domain" =~ ^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$ ]] || [[ "$domain" != *.* ]]; then
  echo 'Usage: sudo bash scripts/deploy-lightsail.sh your.public.hostname' >&2
  exit 2
fi
command -v docker >/dev/null
command -v python3 >/dev/null
docker compose version >/dev/null
docker info >/dev/null
if [[ -e .env.cloud ]]; then
  saved_domain="$(python3 -c 'from pathlib import Path; print(next((s.partition("=")[2] for s in Path(".env.cloud").read_text().splitlines() if s.startswith("APP_DOMAIN=")), ""))')"
  if [[ "$saved_domain" != "$domain" ]]; then
    echo 'Existing .env.cloud uses another hostname. Review that file before changing it.' >&2
    exit 2
  fi
else
  umask 077
  python3 - "$domain" <<'PY'
import secrets
import sys
from pathlib import Path
with Path('.env.cloud').open('x', encoding='utf-8') as stream:
    stream.write('APP_DOMAIN=' + sys.argv[1] + '\nAUTOPILOT_PASSWORD=' + secrets.token_hex(24) + '\n')
PY
fi
chmod 600 .env.cloud
docker compose --project-name clips-kitty-autopilot --env-file .env.cloud -f compose.cloud.yaml config --quiet
docker compose --project-name clips-kitty-autopilot --env-file .env.cloud -f compose.cloud.yaml up --build -d
echo "App containers started. Public address: https://$domain"
echo 'Username: owner. Your private password is in .env.cloud on this server.'
echo 'Certificate setup can take a minute. Ports 80 and 443 must be open in Lightsail.'
echo 'Do not paste .env.cloud or its password into a support chat.'
