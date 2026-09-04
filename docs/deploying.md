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

### Adding a language to the box

Two things per language, and both scripts do every language in
`LL_TEXTREADER_LANGUAGES` and skip whatever is already there, so they are safe to
re-run and safe to interrupt:

```bash
ssh llt@159.195.244.92 'cd /opt/ll-textreader && ./scripts/setup-models.sh'
ssh llt@159.195.244.92 'cd /opt/ll-textreader && ./scripts/setup-dictionary.sh'
```

The **models** are small (fr 63MB, ru 89MB, it 52MB installed) and `deploy.sh`
already reinstalls them on every deploy, because `uv sync` prunes anything not in
the lockfile and the model wheels are not.

The **dictionaries** are the slow part: ~570MB for French, ~940MB for Russian and
~500MB for Italian down the wire, each leaving 12-15MB of glosses behind. Once
only — nothing prunes them — so they are deliberately *not* in `deploy.sh`. Run it
in `tmux` or `screen`; a dropped connection mid-download costs the download, since
each file resumes but the shell that was driving it does not.

Two things to know while it runs:

- **The site stays up.** The database is in WAL mode, so loading glosses does not
  block anyone reading. It is the only writer while it runs, though, so an import
  attempted at the same moment waits for it — do it when nobody is reading.
- **Run it as `llt`, never as root.** A root-owned file in the state directory is
  what stopped the first provisioning run dead (`decisions/0018`).

Until a language's dictionary is loaded, that language reads fine and shows
grammar, and every word says "no dictionary entry". `deploy.sh` prints a note for
any configured language with no glosses, so this cannot sit unnoticed.

### The certificate, and the name

**Real Let's Encrypt certificate, no warning.** It took some getting: the free
netcup hostname shares one quota of fifty new certificates a week with every
other customer on `ultrasrv.de`, and that quota was full, so the box served
Caddy's own CA for a few hours first. The fix was to keep asking — an
`acme`-then-`internal` issuer chain with a one-hour stand-in certificate, so
Caddy retries roughly every forty minutes and falls back meanwhile. It won a
slot on the first retry, at 18:58 UTC on 2 September. `decisions/0020` has the
whole story.

Leave that chain in place. Renewals are exempt from the limit that blocked the
first issue, so this should never recur — but if the certificate ever does lapse,
the fallback means the site keeps serving rather than refusing every handshake.

So a domain of your own now buys two things rather than one: a certificate
without a warning, and the SPF and DKIM that password reset by email
(`decisions/0013`) needs. Five to ten euros a year. When you buy one, point an A
record at 159.195.244.92 and re-run:

```bash
ssh root@159.195.244.92 'LL_TEXTREADER_FQDN=read.example.org bash -s' \
  < scripts/provision.sh
```

That run drops the `tls internal` line from the Caddyfile on its own, so the real
certificate issues on the first request with nothing else to remember.

### What still needs a human

- **Somewhere to put the backups.** The timer runs daily and the script exists;
  what is missing is a destination. Set `LL_TEXTREADER_BACKUP_TO` in `.env` to an
  rsync target that is not this machine — the script says so loudly when it is
  unset, because a backup on the same disk as the database is not a backup.
  **Deliberately deferred on 2 September 2026**, with the risk understood: until
  it is set, one disk failure takes the lexicon with it.
- **A domain**, for a certificate without a warning and for email. See above.
- **Rotating the root password and turning off password logins.** Both left for
  a human on purpose; the two lines are above.

### Deliberately not done

No `ufw`/`nftables` rules. Three things listen: SSH, and Caddy on 80 and 443. The
app itself binds `127.0.0.1` and cannot be reached from outside at all. A firewall
here would be a rule that says "allow the three ports that are open". netcup's own
panel firewall is there if that stops being true.
