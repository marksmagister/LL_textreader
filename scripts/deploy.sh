#!/usr/bin/env bash
# Run this ON the server. Deployment is a pull and a restart.
set -euo pipefail
cd /opt/ll-textreader
. scripts/_config.sh

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
# /api/health is public: there is no shared password any more, and a signed-out
# visitor must be able to reach the sign-in page anyway.
curl -fsS -o /dev/null localhost:8000/api/health && echo "up" || {
  echo "health check failed — check: journalctl -u ll-textreader -n 50" >&2
  exit 1
}

# Not fatal, and not fixed here: the dictionaries are a one-off download of most
# of a gigabyte each, not something to re-run on every deploy. But a language
# offered with no glosses gives a reader grammar and no definitions, and that is
# invisible from the outside — so say it out loud once per deploy.
for lang in $(configured_langs); do
  n=$(glosses "$(configured_db)" "$lang")
  [ "$n" -gt 0 ] || echo "note: no $lang dictionary — ./scripts/setup-dictionary.sh $lang"
done
