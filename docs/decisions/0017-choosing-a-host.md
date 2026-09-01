# 0017 — Choosing a host

## What it actually needs

Measured, not guessed, on the working machine:

| | |
|---|---|
| venv with torch + spaCy model | 918 MB |
| translation model cache | 466 MB |
| database with the French dictionary loaded | 26 MB |
| resident memory, serving, both models loaded | 724 MB |

So: **2 vCPU, 4 GB RAM, 20 GB disk** is the floor, and 40 GB is comfortable. CPU is
what import and translation actually spend; nothing here is IO-bound, and the database
is smaller than a photograph.

## The candidates that fit

| | vCPU | RAM | Disk | €/month |
|---|---|---|---|---|
| Hetzner CX22 | 2 | 4 GB | 40 GB | 3.79 |
| netcup VPS Lite 1 G12s | 2 | 4 GB | 80 GB SSD | 4.88 |
| netcup VPS 500 G12 | 2 | 4 GB ECC | 128 GB NVMe | 5.91 |

All three are enough. The differences are not about whether it runs.

## Decision: netcup VPS 500 G12

2 vCPU, 4 GB DDR5 ECC, 128 GB NVMe, €5.91/month. Rented September 2026.

### What was recommended, and why it was wrong

Hetzner CX22 was recommended first, on tooling and hourly billing. It is on Hetzner's
deprecated list and cannot be ordered — a mistake from trusting pricing articles over
the vendor's own deprecation page. Check availability at the source, not in reviews.

The reasoning below still holds for anyone choosing again; the tooling gap is real and
netcup's API is the weaker one. It is not worth re-litigating for a single box.

### Why Hetzner was preferred, for the record

Three reasons, in order of weight:

1. **Tooling.** `hcloud` is a real CLI and there is a Terraform provider. That is the
   difference between "the host is scriptable" and "the host is a web form", and it is
   the axis that matters most for someone else doing the operating.
2. **Hourly billing, destroy any time.** No commitment at all, not even a month. You
   can throw the box away after a weekend of testing and have paid cents.
3. It is also the cheapest of the three.

Backups: Hetzner snapshots exist, and automated backups cost 20% extra. Neither replaces
copying the database off the machine — see 0006. The disk is the single point of failure
and it lives in the same building as the server.

## On Lite versus regular, now academic

**VPS Lite would have been enough.** The Lite line's stated
compromises are SSD instead of NVMe and reduced bandwidth and interface speed. This app
serves a few kilobytes of JSON per page turn to one reader, and opens a page in 0.08s
against a 26 MB database. NVMe and DDR5 ECC are real advantages in areas this workload
never touches. Paying 21% more for them would be buying a faster disk for a program
that is not waiting on the disk.

Both netcup lines offer hourly billing with no minimum term; the cheaper headline prices
attach to 3, 6 or 12 month variants. Check which variant the basket contains.

## Deliberately not chosen

- **ARM (Hetzner CAX11)** — same price and it would work, but torch and spaCy on
  aarch64 add a class of wheel problems for no gain at this size.
- **Railway / Fly** — less to operate, but a platform charges for the convenience and
  hides the machine, and this project's deployment is meant to be `git pull`.

## When this stops being the right answer

RAM is the first wall. Whisper for real audio alignment (0009) needs several gigabytes
and would mean the 8 GB tier. Both providers resize in place, so this is a decision to
revisit, not one to pre-empt.
