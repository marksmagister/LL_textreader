# Deploying

## Sharing it from this laptop (start here)

No server, no Docker, free:

```bash
./scripts/serve.sh --share
```

That builds the frontend, serves API and pages together on one port, and opens a
Cloudflare tunnel. The `https://….trycloudflare.com` URL it prints is what you send.

Three things to know:

- **The laptop has to be awake and online.** Close the lid and the URL dies. Fine for
  "have a look at this", not for "use it for a week".
- **The URL is public**, and the only door is Google sign-in — so the tunnel needs
  the OAuth client configured, and its redirect URI changes every time the tunnel
  does. Fine for showing someone the reader over your shoulder; awkward as a way to
  let them use it. The box is the answer for that.
- **Quick-tunnel URLs are random and change** every time you restart. There is no
  bookmark; send a fresh link each session.

The server only ever binds `127.0.0.1` — cloudflared runs on the same machine and
connects locally, so nothing else needs to listen on the network.

This used to say that whoever had the URL and the password read *your* lexicon. That
is no longer true: there are accounts now (`decisions/0021`), everyone who signs in
gets their own, and no reader can see another's words. The shared password is gone
entirely.

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

**One pass.** It used to need two: the repo was private, so the first pass stopped
to print a deploy key that had to be added on GitHub before the box could clone.
The repository is public now, the box clones over https, and that step is gone
from the script rather than left in as something to skip. The script is still
idempotent — it checks before every step, so re-running it is also how you resume
after a failed download.

It writes `/opt/ll-textreader/.env` once and never overwrites it. The Google
client id and secret are left **blank** on purpose, and the box serves nobody
until they are filled in: a secret is the one value that must not be generated or
guessed, so the script says what to paste rather than inventing something. See
*Google sign-in* below.

### First, rotate the root password

netcup emailed it in plaintext, so treat it as public and change it before
anything else. The box has a routable IPv4 address and will be finding out about
SSH brute-forcers within the hour.

**This got more urgent when the repository went public, 3 September 2026.** This
file is now readable by anyone, and taken together it says: here is the address,
here are two account names, password authentication is still accepted, and the
root password may still be the one netcup emailed. That is not a leak — every
part of it was already discoverable, since the hostname resolves to the address
and appears in the app's own OAuth redirect URI — but it is now collected in one
place with instructions. Redacting it would buy nothing and cost the record; the
fix is to make the sentence untrue. **Do the two lines below and the hardening in
*What still needs a human* before leaving the box another night.**

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

### Google sign-in

Google is the only way in (`decisions/0021`), so the box cannot serve anybody
until an OAuth client exists and its two values are in `.env`.

The project's client id, which is public by design — it travels in the redirect
URL and is visible in every reader's browser, so it is recorded here rather than
being something to go and look up:

```
369455894872-l6t0vlbfc6kbaar7fhihqj02sr7vc4kr.apps.googleusercontent.com
```

The **client secret is not public** and must never be committed. It goes straight
into `/opt/ll-textreader/.env` on the box and nowhere else — not into git, not
into a chat window, not into an issue.

The support address is a Google Group, `ll_textreader@googlegroups.com`, and the
reason is worth keeping: *User support email* on the consent screen is a
dropdown, not a text field, and Google only offers the logged-in account's own
address or a group it manages. A personal address would work and would then sit
on the consent screen and — worse — on the privacy and terms pages, which are
public and get scraped. The group takes the spam instead, and can be moderated
or deleted without touching anyone's inbox. It is the address in
`legal/privacy.html` and `legal/terms.html` too.

**A new Google Group rejects mail from non-members by default**, which would make
the support address look fine and silently bounce every reader who wrote to it.
Set posting permission to anyone on the web, and send it a message from an
unrelated account once to prove it arrives.

Four things to set in [console.cloud.google.com](https://console.cloud.google.com):

1. **Register the redirect URI on the OAuth client, exactly.** Google compares it
   as a string, so a missing slash is a `redirect_uri_mismatch` and nothing else.
   Both of these can be registered at once, which is what lets you test locally
   against the same client:

   ```
   https://v2202609408983511171.ultrasrv.de/api/auth/google/callback
   http://localhost:8000/api/auth/google/callback
   ```

   `http` is allowed for `localhost` specifically, and for nothing else.

2. **Scopes: `openid`, `email`, `profile`. Nothing else.** These are Google's
   non-sensitive scopes, and using only them is what lets this app publish
   without a verification review. Adding a fourth scope is not a small change —
   it can put the project into a review queue.

3. **Stay in Testing, and add each reader by hand.** Audience page →
   *Test users* → **Add users**, one Google address per person:
   `console.cloud.google.com/auth/audience?project=ll-textreader`. Up to 100.
   Only addresses on that list can sign in at all, which makes the list the
   access control — there is no invite table in this codebase because this is it.

   **Do not copy that list into this repository.** The repo is public, and a file
   of testers' addresses would publish the email addresses of people who agreed
   to try a reading app. It lives in the console and nowhere else.

4. **Upload the logo** — `frontend/public/brand/logo-120.png`. Google requires
   verification for a logo *unless* the status is Testing, so staying in Testing
   is what makes this free.

**About the seven-day consent expiry, because it sounds worse than it is here.**
Google expires a test user's *OAuth grant* after seven days. That is severe for an
app holding a refresh token to call Google while the user is away — it would break
weekly. This app holds none: `google.py` never asks for offline access, stores no
refresh token, and does not call Google again after the one code exchange at
sign-in. Readers are carried by our own session cookie for `session_days`, ninety
by default. The only visible effect is that somebody signing in again more than a
week later sees the consent screen once more. One extra click, on a re-login.

An earlier version of this file said readers "would be signed out weekly" and told
you to publish immediately. That was wrong for this application, and the mistake
was reasoning about OAuth in general rather than about what this code actually does.

### If this is ever opened to the public

Publishing removes the 100-place ceiling and the hand-kept list. It also brings two
things Testing avoids, so it is a decision rather than a step:

- **A logo then needs brand verification**, which checks ownership of the domain on
  the consent screen. `ultrasrv.de` is netcup's, not ours, so that review cannot pass
  until there is a domain of our own.
- **A postal address becomes necessary.** The Impressum duty bites on a service
  offered to the public; a hand-kept list of people is not that. `docs/status.md`
  carries the reasoning and what it costs.

The button is on the **Audience** page, not Branding. The old console put it under
APIs & Services → OAuth consent screen; that page no longer exists, since the 2025
reorganisation split it into Branding, Audience, Clients and Data Access. Two things
gate it quietly: branding must be complete and saved first, or it refuses with *"Your
app's OAuth configuration is incomplete"*; and user type must be External, because
internal apps never publish.

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
