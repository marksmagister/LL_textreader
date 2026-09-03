"""A web page -> the text worth reading.

Import friction is what kills the habit, and the text you want is usually behind
a URL rather than already in a file. trafilatura does the extraction; everything
here is about not fetching things we shouldn't.
"""

import http.client
import ipaddress
import socket
import urllib.request
from urllib.parse import urlparse

# A page that will not fit on a screen will not fit in a lesson either, and the
# body is read into memory before anything looks at it.
MAX_BYTES = 4_000_000
TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; LL_textreader)"


class BadUrl(Exception):
    pass


def check(url: str) -> str:
    """Refuse anything that isn't a public web page.

    The server does the fetching, so a URL is an instruction to make a request
    from inside wherever this is hosted. Without this, anyone who can reach the
    app can use it to probe localhost, the private network, or a cloud metadata
    endpoint — and read the result back as a lesson.

    Called on the address you typed *and on every redirect it leads to* — see
    `_GuardedRedirects`. Checking only the first one is checking nothing: a
    public page is free to answer "302, go and read 169.254.169.254".
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise BadUrl("only http and https")
    if not parsed.hostname:
        raise BadUrl("no host")

    resolve(parsed.hostname)
    return url


def resolve(hostname: str) -> str:
    """Resolve a name and return one address, refusing anything not public.

    Every rejection here is a place the app could otherwise be pointed at
    something only it can reach: loopback, the private network, and above all
    169.254.169.254 — the cloud metadata service, which hands credentials to
    anything that asks from the right machine.
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise BadUrl(f"cannot resolve {hostname}") from exc

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        # link-local covers 169.254.169.254, which is the cloud metadata service
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise BadUrl(f"{hostname} resolves to a non-public address")
    if not infos:
        raise BadUrl(f"cannot resolve {hostname}")
    return infos[0][4][0]


# ---------------------------------------------------------------- DNS rebinding
#
# `check` used to resolve the name, and then urllib resolved it *again* to open
# the socket. A domain whose record flips between those two lookups passes the
# check and gets connected to anyway — classic rebinding, and 0019 left it open
# on the grounds that whoever could reach this had already been invited.
#
# Signup is open now, so that reasoning is gone: anyone with a Google account can
# make this server fetch an address of their choosing.
#
# The fix is not a better check. It is that there is now only **one** lookup:
# these connection classes resolve and validate at the moment they connect, and
# connect to that exact address, so there is no window between deciding and
# doing. The name is still what TLS verifies against — `server_hostname` carries
# it into the handshake — so pinning the address costs no certificate checking,
# which is what 0019 worried it would.


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def connect(self) -> None:
        self.sock = socket.create_connection((resolve(self.host), self.port), self.timeout)
        if self._tunnel_host:
            self._tunnel()


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def connect(self) -> None:
        sock = socket.create_connection((resolve(self.host), self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
            sock = self.sock
        # server_hostname is the *name*, not the address we connected to, so the
        # certificate is still checked against the site the reader asked for.
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


class _PinnedHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(_PinnedHTTPConnection, req)


class _PinnedHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_PinnedHTTPSConnection, req, context=self._context)


class _GuardedRedirects(urllib.request.HTTPRedirectHandler):
    """Re-run `check` at every hop, so a redirect can't step over it.

    Still needed alongside the pinning above: pinning stops the address changing
    under a name we approved, and this stops us being sent to a different name
    altogether. A public page is free to answer "302, go and read
    169.254.169.254", and that needs no cooperation from the person pasting the
    link — which is what made redirects the more urgent half in 0019.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download(url: str) -> str:
    """The page's HTML. Ours rather than trafilatura's, so that redirects go
    through `check` and every connection resolves through `resolve`."""
    opener = urllib.request.build_opener(
        _PinnedHTTPHandler, _PinnedHTTPSHandler, _GuardedRedirects
    )
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            check(response.geturl())  # belt and braces: whatever we ended up at
            raw = response.read(MAX_BYTES + 1)
            charset = response.headers.get_content_charset() or "utf-8"
    except BadUrl:
        raise
    except OSError as exc:
        raise BadUrl(f"could not fetch that page: {exc}") from None
    if len(raw) > MAX_BYTES:
        raise BadUrl("that page is too big to import")
    return raw.decode(charset, errors="replace")


def fetch(url: str) -> tuple[str, str | None]:
    """Return (text, title). Raises BadUrl when there is nothing worth importing."""
    try:
        import trafilatura
    except ImportError as exc:  # pragma: no cover - a broken install, not a bad url
        raise BadUrl("URL import needs trafilatura: uv sync") from exc

    check(url)
    html = _download(url)

    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not text or not text.strip():
        raise BadUrl("no article text found on that page")

    meta = trafilatura.extract_metadata(html)
    return text, (meta.title if meta else None)
