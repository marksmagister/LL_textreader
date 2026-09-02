# 0018 — Provisioning the box

`0017` chose the machine. This is what happened when it arrived, and the four
things that were not what `deploying.md` had assumed.

## It came with Debian 13, and it is staying

The build instructions specified Ubuntu 24.04. netcup delivered Debian 13
(trixie) minimal. Reinstalling was offered and declined, because on the one axis
that actually differs Debian is the better box:

| | Node in the archive | Python in the archive |
|---|---|---|
| Debian 13 trixie | 20.19.2 | 3.13 |
| Ubuntu 24.04 noble | 18.19.1 | 3.12 |

Vite 8, `@vitejs/plugin-react` 6 and oxlint all declare
`node: ^20.19.0 || >=22.12.0`. Trixie satisfies that with 20.19.2 — by two patch
releases, but it satisfies it. **Ubuntu 24.04's Node 18 does not**, so the
"matching" distribution would have needed a third-party Node repo on day one.

Ubuntu's apparent advantage is the reverse case: it ships Python 3.12, which is
what `pyproject.toml` pins (`>=3.12,<3.13`, because spaCy lags CPython), and
trixie ships 3.13. That advantage is worth nothing, because `uv python install
3.12` fetches the interpreter regardless. The Python version is the repo's to
declare, not the distribution's to supply — which was already true on the laptop.

So: an hour of reinstalling to trade a solved problem for an unsolved one. No.

Node is only ever used to *build* the frontend — uvicorn serves the result — so
its EOL status is a build-time concern, not an exposed one. If a future Vite
wants Node 22, that is the day to add NodeSource, and not before.

## Caddy is not in Debian

`apt install caddy` fails on trixie; it is not in the archive. `provision.sh` adds
the upstream Cloudsmith repo. This is the one third-party apt source on the box.

## The hostname problem solved itself

`deploying.md` had TLS blocked on "pick a hostname", with DuckDNS as the plan.
Unnecessary: netcup points `v2202609408983511171.ultrasrv.de` at the box already,
and it resolves. Caddy will get a Let's Encrypt certificate for it on the first
request, so the pilot needs no DNS work, no DuckDNS account and no purchase.

The limitation that made DuckDNS awkward still applies, unchanged and no worse: it
is not a domain anyone here owns, so it can never carry SPF or DKIM, and email
password reset (`0013`) still needs a real domain. That is a purchase to make when
email matters, not a blocker on getting the thing hosted.

## The repo is private, so provisioning is two passes

`git clone https://github.com/…` was going to fail on the box. The fix is a
read-only deploy key, and the awkward part is the chicken-and-egg: the script that
sets the box up lives in the repo the box cannot read yet.

Resolved by shipping the script *over the wire* rather than fetching it —
`ssh root@box 'bash -s' < scripts/provision.sh` — and by making the script
idempotent and stop-and-resume. The first pass does everything that needs no repo,
generates a key, prints it, and exits 0. You add it to GitHub and run the same
command again.

Idempotence was going to be worth having anyway. The dictionary is a 573MB
download and torch is most of a gigabyte; a provisioning run that cannot be
resumed after a dropped connection is a provisioning run you do from scratch.

## Two bugs this turned up

- **`deploy.sh` would have reported failure on every successful deploy.** Its
  health check was an unauthenticated `curl` to `/api/health`, and that endpoint
  is behind the shared password like everything else, so a working server answers
  401 and `curl -f` exits non-zero. It now sources `.env` and sends the password.
- **The service unit ran `uv run` under `ProtectHome=read-only`.** uv wants its
  cache under `/home/llt` at every start. `ExecStart` is now the venv's own
  `uvicorn` binary, which removes uv from the runtime path entirely. `--app-dir
  backend` stays, and is load-bearing: it puts `backend/` ahead of site-packages
  so `config.py` computes the repo root correctly and finds the built frontend.

## No firewall, deliberately

SSH, and Caddy on 80 and 443. The app binds `127.0.0.1` and is unreachable from
outside except through Caddy. `ufw` here would be a rule listing the ports that
are already the only ones open. netcup's panel firewall exists if that changes.

## The credentials it shipped with

netcup emails the root password in plaintext, so it is compromised on arrival and
`deploying.md` says to rotate it first. Nothing from that email is in this repo,
and the generated app password lives only in `/opt/ll-textreader/.env`, mode 600.
