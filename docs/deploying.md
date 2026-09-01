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

## Later: a real host

`git pull` + `docker compose up -d --build`. Keep it that way.

One container serves the API and the built frontend on one port; Caddy sits in front
for TLS and a password. Decision 0005 explains why this is a web app and not a Mac app.

## First time

```bash
cp Caddyfile Caddyfile.local   # edit the hostname and password hashes
docker compose up -d --build
```

Password hashes:

```bash
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'your-password'
```

The dictionary is not in the image — it is 573MB of download that leaves 12MB of
glosses. Load it once, into the running container:

```bash
docker compose exec reader ./scripts/setup-dictionary.sh fr
```

## Sharing it

The app is **single-user by design**: `USER_ID = 1`, one lexicon, one library. Anyone
with the URL reads with your vocabulary and sees your words. For showing a friend the
pilot, that is the point. It is not a login system and must never be treated as one.

To give someone a lexicon of their own, copy the `reader` service in
`docker-compose.yml` under a new name with its own volume, and add a host to the
Caddyfile. Two containers, no auth code. Real multi-user is deliberately out of v1.

## Backups

```bash
./scripts/backup.sh
```

Uses `sqlite3 .backup`, which is safe against a live WAL database — plain `cp` can
capture a torn state. Back up the *lexicon*: the lessons are replaceable, but
`lemma_status` and `form_seen` are months of reading.

## After a model or rule change

`pipeline_id` records which pipeline produced each token stream. When it moves:

```bash
docker compose exec reader uv run python -m ll_textreader.importers.plain_text --dry-run
docker compose exec reader uv run python -m ll_textreader.importers.plain_text
```

The body is never touched and the lexicon is keyed on lemma, so nothing is lost;
saved reading positions are carried across by character offset.

## Untested

The image build has not been run — Docker was not available on the machine these
files were written on. The single-port serving they rely on **was** verified.
