# Deploying

## Sharing it from this laptop (start here)

No server, no Docker, free:

```bash
echo 'LL_TEXTREADER_PASSWORD=something-long' >> .env   # once
./scripts/serve.sh --share
```

That builds the frontend, serves API and pages together on one port, and opens a
Cloudflare tunnel. The `https://….trycloudflare.com` URL it prints is what you send.

Three things to know:

- **The laptop has to be awake and online.** Close the lid and the URL dies. Fine for
  "have a look at this", not for "use it for a week".
- **The URL is public**, so the password is the only door. `--share` refuses to start
  without one, deliberately.
- **Quick-tunnel URLs are random and change** every time you restart. There is no
  bookmark; send a fresh link each session.

The server only ever binds `127.0.0.1` — cloudflared runs on the same machine and
connects locally, so nothing else needs to listen on the network.

There are no accounts. Whoever has the URL and password reads *your* lexicon and sees
what you have read. That is what makes it a demo rather than a product.

## The real host

A netcup VPS 500 G12 (2 vCPU, 4 GB, 128 GB NVMe, hourly-billed). Ubuntu 24.04.
Deployment is `git pull` and a restart — no image build, no registry, no daemon in
between. See `decisions/0010-choosing-a-host.md` for why this box.

### Once, to build the machine

```bash
adduser --disabled-password --gecos '' llt
apt update && apt install -y git curl caddy nodejs npm python3.12-venv
su - llt -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'

git clone https://github.com/marksmagister/LL_textreader /opt/ll-textreader
chown -R llt:llt /opt/ll-textreader
mkdir -p /var/lib/ll-textreader && chown llt:llt /var/lib/ll-textreader

# The password, and where the database lives. Never in the repo.
cat >> /opt/ll-textreader/.env <<'ENV'
LL_TEXTREADER_DB_PATH=/var/lib/ll-textreader/ll_textreader.db
LL_TEXTREADER_DATA_DIR=/var/lib/ll-textreader
LL_TEXTREADER_PASSWORD=<something long>
ENV

su - llt -c 'cd /opt/ll-textreader && uv sync --extra nlp --extra translate --no-dev'
su - llt -c 'cd /opt/ll-textreader && ./scripts/setup-models.sh fr'
su - llt -c 'cd /opt/ll-textreader && ./scripts/setup-dictionary.sh fr'

cp deploy/ll-textreader.service /etc/systemd/system/
systemctl enable --now ll-textreader

cp deploy/Caddyfile /etc/caddy/Caddyfile   # edit the hostname first
systemctl reload caddy
```

### Every time after that

```bash
ssh llt@the-box '/opt/ll-textreader/scripts/deploy.sh'
```

### What still needs a human

- **A domain name.** Caddy gets a certificate automatically, but only for a name that
  resolves to the box. Without one you are on `https://<ip>` with a self-signed
  certificate and a browser warning, which is not something to hand a friend.
- **Backups off the machine.** `scripts/backup.sh` on a cron, and the result copied
  somewhere that is not this disk. The lexicon is the one thing here that cannot be
  rebuilt, and it sits on a single volume in a single building.
