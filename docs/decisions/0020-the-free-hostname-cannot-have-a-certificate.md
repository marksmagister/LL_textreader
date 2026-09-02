# 0020 — The free hostname cannot have a certificate

**Status: accepted. Caddy serves its own certificate; a real one waits on a domain.**

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

`tls internal` in the Caddyfile: Caddy runs its own CA, issues its own certificate,
and serves HTTPS with a browser warning. One reader who clicks through once per
browser, in exchange for encryption today.

## Why not the alternatives

- **Wait for a slot.** Caddy retries with backoff for thirty days and might well
  succeed — the 429 names a time when the window rolls. But it is a lottery against
  every other netcup customer, and the certificate expires in sixty days, so it is a
  lottery you re-enter six times a year. Losing means the app is unreachable rather
  than ugly, which is worse.
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

`provision.sh` deletes the `tls internal` line for any name that is not
`*.ultrasrv.de`, so a real certificate issues on the first request with nothing else
to remember. That is deliberate: leaving the browser warning in place after buying a
domain is exactly the sort of thing that costs an hour to diagnose.

A domain was already on the list for a second reason — `0013`'s password reset needs
SPF and DKIM, and you cannot publish either on a name you do not own. This makes it
two reasons for the same five to ten euros a year.
