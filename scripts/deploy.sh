#!/usr/bin/env bash
# Run this ON the server. Deployment is a pull and a restart.
set -euo pipefail
cd /opt/ll-textreader

echo "Backing up first — a deploy is exactly when you want yesterday's lexicon."
./scripts/backup.sh

git pull --ff-only
uv sync --extra nlp --extra translate --no-dev

# uv sync prunes anything not in the lockfile, and the spaCy models are installed
# as wheels that are not. Re-download them every time rather than debug it later.
# No argument means every language in LL_TEXTREADER_LANGUAGES — this said `fr`
# once, and adding a language without noticing would have removed its model on
# the next deploy and left the box answering 503 for it.
./scripts/setup-models.sh

npm --prefix frontend ci
npm --prefix frontend run build

sudo systemctl restart ll-textreader
sleep 3
# /api/health is behind the shared password like everything else, so the check
# has to carry it — without this a healthy deploy reports failure on a 401.
[ -f .env ] && set -a && . ./.env && set +a
curl -fsS -u "${LL_TEXTREADER_USERNAME:-read}:${LL_TEXTREADER_PASSWORD:-}" \
     -o /dev/null localhost:8000/api/health && echo "up" || {
  echo "health check failed — check: journalctl -u ll-textreader -n 50" >&2
  exit 1
}
