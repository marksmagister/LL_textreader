#!/usr/bin/env bash
# Run the whole app on one port: API and built frontend together.
#
#   ./scripts/serve.sh              local only, no password needed
#   ./scripts/serve.sh --share      also opens a public Cloudflare tunnel
#
# The tunnel makes this laptop reachable from the internet, so --share refuses
# to start without LL_TEXTREADER_PASSWORD. Binding stays on 127.0.0.1 either
# way: cloudflared runs here and connects locally, so nothing else needs to.
set -euo pipefail
cd "$(dirname "$0")/.."

port="${PORT:-8000}"
share=""
[ "${1:-}" = "--share" ] && share=1

# .env is where the password lives, and it is gitignored.
[ -f .env ] && set -a && . ./.env && set +a

if [ -n "$share" ] && [ -z "${LL_TEXTREADER_PASSWORD:-}" ]; then
  cat >&2 <<'MSG'
Refusing to open a tunnel with no password.

A tunnel puts this laptop on the public internet, and without a password anyone
with the URL reads your vocabulary and everything you have read. Set one:

    echo 'LL_TEXTREADER_PASSWORD=something-long' >> .env

MSG
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
