#!/usr/bin/env bash
# Run the whole app on one port: API and built frontend together.
#
#   ./scripts/serve.sh              local only
#   ./scripts/serve.sh --share      also opens a public Cloudflare tunnel
#
# The shared password is gone (docs/decisions/0021) — the door is Google sign-in
# now, and the thing --share has to check is that signing in actually works.
# Without it a tunnel serves a public URL nobody can get into, which looks like
# the app is broken. Binding stays on 127.0.0.1 either way: cloudflared runs
# here and connects locally, so nothing else needs to.
set -euo pipefail
cd "$(dirname "$0")/.."

port="${PORT:-8000}"
share=""
[ "${1:-}" = "--share" ] && share=1

# .env is where the Google credentials live, and it is gitignored.
[ -f .env ] && set -a && . ./.env && set +a

if [ -n "$share" ] && [ -z "${LL_TEXTREADER_GOOGLE_CLIENT_ID:-}" ]; then
  cat >&2 <<'MSG'
Refusing to open a tunnel with no way to sign in.

A tunnel puts this laptop on the public internet. Signing in is the only door,
so without Google configured the URL you hand out is one nobody can open — and
that reads as a broken app rather than a closed one.

Set these in .env, from an OAuth client at console.cloud.google.com:

    LL_TEXTREADER_GOOGLE_CLIENT_ID=...
    LL_TEXTREADER_GOOGLE_CLIENT_SECRET=...
    LL_TEXTREADER_GOOGLE_REDIRECT_URI=https://<the tunnel host>/api/auth/google/callback

The redirect URI has to match one registered on that client exactly, and a
quick-tunnel hostname changes every run — which is why a real host is easier.

MSG
  exit 1
fi

# Cookies are Secure by default and a browser ignores those over plain http.
# Local development has no TLS, so without this nobody can stay signed in.
if [ -z "$share" ]; then
  export LL_TEXTREADER_COOKIE_SECURE=false
fi

# `uv sync` prunes anything not in the lockfile, and the spaCy model is installed
# by `spacy download` rather than declared as a dependency — so syncing silently
# removes it and every import fails at runtime. Catch it here instead.
if ! uv run python -c "import fr_core_news_md" 2>/dev/null; then
  echo "The French model is missing (uv sync removes it). Run:" >&2
  echo "    ./scripts/setup-models.sh fr" >&2
  exit 1
fi

echo "Building the frontend…"
npm --prefix frontend run build >/dev/null

if [ -n "$share" ]; then
  command -v cloudflared >/dev/null || { echo "brew install cloudflared" >&2; exit 1; }
  uv run uvicorn ll_textreader.main:app --app-dir backend --host 127.0.0.1 --port "$port" &
  api=$!
  trap 'kill $api 2>/dev/null' EXIT
  sleep 2
  echo "Opening a tunnel. The https:// URL below is what you share."
  cloudflared tunnel --url "http://localhost:$port"
else
  exec uv run uvicorn ll_textreader.main:app --app-dir backend \
       --host 127.0.0.1 --port "$port"
fi
