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

A netcup VPS 500 G12 (2 vCPU, 4 GB ECC, 128 GB NVMe, hourly-billed) in Vienna,
running **Debian 13 (trixie), minimal**. Provisioned September 2026.

```
159.195.244.92            v2202609408983511171.ultrasrv.de
2a0a:4cc0:61:1b76:587f:fdff:fec3:d30c
```

Why Debian and not the Ubuntu 24.04 this file used to specify: see
`decisions/0018-provisioning-the-box.md`. Short version — trixie ships the Node
that Vite 8 requires and Ubuntu 24.04 does not, and Python comes from `uv` either
way, so there is nothing to gain by reinstalling.

### Building it

```bash
ssh root@159.195.244.92 'bash -s' < scripts/provision.sh
```

That is the whole thing. It installs the packages, adds Caddy's repo, creates the
`llt` user, gets Python 3.12 through `uv`, clones, builds, and starts the service
and the backup timer behind TLS.

**It needs two passes.** The repo is private, so the box cannot clone it until it
has a key of its own. The first pass stops and prints one; add it at
[Settings → Deploy keys](https://github.com/marksmagister/LL_textreader/settings/keys/new)
(read-only — it never pushes), then run the same command again. The script is
idempotent: it checks before every step, so re-running it is also how you resume
after a failed download.

It writes `/opt/ll-textreader/.env` once, with a generated password, and prints
that password exactly once. It will not overwrite it on a later run — regenerating
it would lock you out of your own lexicon.

### First, rotate the root password

netcup emailed it in plaintext, so treat it as public and change it before
anything else. The box has a routable IPv4 address and will be finding out about
SSH brute-forcers within the hour.

```bash
ssh root@159.195.244.92     # the password from netcup's email
passwd                      # pick a new one
```

`provision.sh` installs the maintainer's public key for both `llt` and `root`, so
after it has run you can reach the box without a password at all. Once
`ssh llt@159.195.244.92` works, close the front door:

```bash
printf 'PermitRootLogin prohibit-password\nPasswordAuthentication no\n' \
  > /etc/ssh/sshd_config.d/harden.conf
systemctl restart ssh
```

Do that in a second terminal while the first stays logged in, so a typo is
recoverable rather than a trip to netcup's web console.

### Every time after that

```bash
ssh llt@159.195.244.92 '/opt/ll-textreader/scripts/deploy.sh'
```

Pull, sync, rebuild, restart, health-check. `provision.sh` gives `llt` exactly one
root privilege — restarting this one service — which is all `deploy.sh` needs.

### The certificate, and the name

Caddy gets a real Let's Encrypt certificate on the first request, because
`v2202609408983511171.ultrasrv.de` is a name netcup already points at the box.
No DuckDNS, no self-signed warning, nothing to buy. That is enough for the pilot.

It is still not a name you would put on a poster, and it is not a domain *you*
own, so it can never carry SPF or DKIM — password reset by email
(`decisions/0013`) needs a real domain, five to ten euros a year. When you buy
one, point it at the box and re-run:

```bash
ssh root@159.195.244.92 'LL_TEXTREADER_FQDN=read.example.org bash -s' \
  < scripts/provision.sh
```

### What still needs a human

- **Somewhere to put the backups.** The timer runs daily and the script exists;
  what is missing is a destination. Set `LL_TEXTREADER_BACKUP_TO` in `.env` to an
  rsync target that is not this machine — the script says so loudly when it is
  unset, because a backup on the same disk as the database is not a backup.
- **A domain**, if email ever matters. See above.

### Deliberately not done

No `ufw`/`nftables` rules. Three things listen: SSH, and Caddy on 80 and 443. The
app itself binds `127.0.0.1` and cannot be reached from outside at all. A firewall
here would be a rule that says "allow the three ports that are open". netcup's own
panel firewall is there if that stops being true.
