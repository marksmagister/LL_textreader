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

### Where this stands, and what it is waiting for

Rented September 2026, hourly-billed, no minimum term. **Not yet provisioned.** Three
things have to happen, in order, and the first two need a human:

1. Install Ubuntu 24.04 from netcup's server control panel, giving it this key:

   ```
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBK12YUpwWHoOAp8sEczaZfG6qRyzRJcy2UauY5eNF60 ll-textreader deploy
   ```

   The matching private key is at `~/.ssh/ll_textreader_deploy` on the maintainer's
   laptop and has never left it. Regenerate with `ssh-keygen -t ed25519` if lost — the
   server-side half is replaceable.

2. **A hostname.** DuckDNS was chosen for now: free, and Caddy can get a certificate
   for a `*.duckdns.org` subdomain. Put it in the `Caddyfile` in place of
   `read.example.com`.

   Note the limit: SPF and DKIM are DNS records on a domain *you own*, so a DuckDNS
   subdomain can never send email. If password reset by email is ever wanted
   (`decisions/0013`), that needs a real domain — five to ten euros a year, and a
   better URL to post anyway.

3. Then the build steps below, and `scripts/deploy.sh` from then on.

Until it is up, `./scripts/serve.sh --share` on the laptop is what exists.
Deployment is `git pull` and a restart — no image build, no registry, no daemon in
between. See `decisions/0017-choosing-a-host.md` for why this box.

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
- **Somewhere to put the backups.** The timer and the script exist; what is missing is
  a destination. Set `LL_TEXTREADER_BACKUP_TO` to an rsync target that is not this
  machine — the script says so loudly when it is unset, because a backup on the same
  disk as the database is not a backup.

```bash
cp deploy/ll-textreader-backup.{service,timer} /etc/systemd/system/
systemctl enable --now ll-textreader-backup.timer
```
