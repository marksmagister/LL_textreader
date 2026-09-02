# 0020 — The free hostname cannot have a certificate

**Status: resolved. The hostname has a real Let's Encrypt certificate.**

Outcome first, because the title is now half wrong: it took four hours and three
attempts, but `v2202609408983511171.ultrasrv.de` got a public certificate at
18:58:52 UTC on 2 September 2026, valid to 1 December, and the chain validates
with no `-k`. Persistence was the answer; the title stays as it was written so
the reasoning below reads in the order it happened.

`0018` provisioned the box and `deploying.md` promised that Caddy would get a real
Let's Encrypt certificate on the first request, "because
`v2202609408983511171.ultrasrv.de` is a name netcup already points at the box. No
DuckDNS, no self-signed warning, nothing to buy." That was wrong, and the reason is
worth writing down, because it is not obvious and it will come back at renewal time.

## What happened

The site came up on 443 and every TLS handshake failed with an internal-error alert —
Caddy's signature for "I have no certificate and cannot get one". The log:

```
HTTP 429 urn:ietf:params:acme:error:rateLimited - too many certificates (50)
already issued for "ultrasrv.de" in the last 168h0m0s
```

Let's Encrypt counts new certificates **per registered domain**, not per hostname.
`ultrasrv.de` is netcup's, and every customer who leaves their VPS on its default
`v…​.ultrasrv.de` name draws from the same 50-a-week bucket. A provider with more
than fifty customers provisioning in any given week keeps that bucket permanently
empty. Providers who care get their hostname domain onto the Public Suffix List,
which splits the limit per customer; netcup has not.

Nothing was wrong with the setup. Caddy fell back to the staging CA, which has no
such limit, solved the same HTTP-01 challenge against the same box and issued
immediately — so DNS, port 80, the challenge and the reload were all correct. The
only broken thing was the quota, and it is not ours to fix.

## What we did

An issuer chain, `acme` then `internal`, with the internal certificate given a
one-hour lifetime. Caddy asks Let's Encrypt first, falls back to its own CA when the
answer is 429, and — because it walks the chain again whenever the certificate it is
serving needs renewing — asks again roughly every forty minutes. The site is up the
whole time, with a browser warning, and the warning disappears on its own the first
time an ask lands. Nothing to run, nothing to remember.

**Correction, same day.** The first version of this file said `tls internal` and
argued that waiting was a bad trade because "the certificate expires in sixty days,
so it is a lottery you re-enter six times a year". That is wrong, and it is the whole
reason the decision changed. Let's Encrypt's own documentation exempts renewals from
this limit: an order with an identical set of identifiers is exempt from New
Certificates per Registered Domain, and an ARI-coordinated renewal — which is what
Caddy does, the logs show it fetching renewal info — is "exempt from all rate
limits". So the lottery is entered **once**. After the first certificate, this
hostname renews like any other. That makes persistent retrying the right answer and
giving up permanently the wrong one.

**What actually happened.** The retry chain went in at 18:35 UTC. Caddy's
existing stand-in certificate had another four hours to run, so the first retry
did not fire until that certificate came up for renewal at 18:56 — and it won the
slot immediately, at 18:58:52. One attempt. Which says the bucket was not as
contested as the 429 made it feel: the window named in the error had rolled at
12:30 UTC, and nobody had taken the freed slot in the six hours since. A poller
beats a one-shot, and most netcup customers only ask once.

That is a single observation, not a measurement. It says nothing about how long
the next box would wait.

One thing deliberately not claimed here: how contested the bucket actually is.
Certificate Transparency was the obvious way to measure it, but two crt.sh queries
for `%.ultrasrv.de` returned different, truncated result sets — one implying no new
hostname had been certified since 2020, which cannot be true alongside a 429 saying
fifty were issued this week. A number that disagrees with itself does not go in a
decision file.

## Why not the alternatives

- **Give up on a real certificate.** What the first version of this decision did.
  Wrong for the reason corrected above: the cost of waiting is one browser warning,
  not a recurring outage, and the reward is permanent.
- **A free subdomain** (DuckDNS and friends). Rejected in `deploying.md` already; it
  trades one domain you do not control for another, and adds an account.
- **A different CA.** ZeroSSL and Google Trust Services have their own limits and
  both need an account with external-account binding credentials to configure. More
  moving parts than buying a domain.

## The real fix, when it is worth five euros

Buy a domain, point an A record at 159.195.244.92, and re-run:

```bash
ssh root@159.195.244.92 'LL_TEXTREADER_FQDN=read.example.org bash -s' \
  < scripts/provision.sh
```

No special case in `provision.sh` for that: one Caddyfile is correct for both names,
because a domain of your own gets its certificate from the first issuer and never
reaches the second.

A domain was already on the list for a second reason — `0013`'s password reset needs
SPF and DKIM, and you cannot publish either on a name you do not own. This makes it
two reasons for the same five to ten euros a year.
