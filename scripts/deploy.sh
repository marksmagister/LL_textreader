#!/usr/bin/env bash
# Run this ON the server. Deployment is a pull and a restart.
set -euo pipefail
cd /opt/ll-textreader

# uv installs itself here, and `ssh box ./deploy.sh` runs a non-interactive shell
# that never reads the profile which adds it. provision.sh spells the path out
# every time; this is the same fix once, for everything below.
PATH="$HOME/.local/bin:$PATH"

echo "Backing up first — a deploy is exactly when you want yesterday's lexicon."
./scripts/backup.sh

git pull --ff-only
uv sync --extra nlp --extra translate --no-dev

# uv sync prunes anything not in the lockfile, and the spaCy model is installed
# as a wheel that is not. Re-download it every time rather than debug it later.
./scripts/setup-models.sh fr

npm --prefix frontend ci
npm --prefix frontend run build

sudo systemctl restart ll-textreader
sleep 3
# /api/health is public: there is no shared password any more, and a signed-out
# visitor must be able to reach the sign-in page anyway.
curl -fsS -o /dev/null localhost:8000/api/health && echo "up" || {
  echo "health check failed — check: journalctl -u ll-textreader -n 50" >&2
  exit 1
}
