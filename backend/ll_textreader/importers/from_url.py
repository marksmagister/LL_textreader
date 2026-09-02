"""A web page -> the text worth reading.

Import friction is what kills the habit, and the text you want is usually behind
a URL rather than already in a file. trafilatura does the extraction; everything
here is about not fetching things we shouldn't.
"""

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

    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise BadUrl(f"cannot resolve {parsed.hostname}") from exc

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        # link-local covers 169.254.169.254, which is the cloud metadata service
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise BadUrl(f"{parsed.hostname} resolves to a non-public address")
    return url


class _GuardedRedirects(urllib.request.HTTPRedirectHandler):
    """Re-run `check` at every hop, so a redirect can't step over it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download(url: str) -> str:
    """The page's HTML. Ours rather than trafilatura's, only so that redirects
    go through `check` — trafilatura follows them itself and would not."""
    opener = urllib.request.build_opener(_GuardedRedirects)
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
