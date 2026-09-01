"""A web page -> the text worth reading.

Import friction is what kills the habit, and the text you want is usually behind
a URL rather than already in a file. trafilatura does the extraction; everything
here is about not fetching things we shouldn't.
"""

import ipaddress
import socket
from urllib.parse import urlparse


class BadUrl(Exception):
    pass


def check(url: str) -> str:
    """Refuse anything that isn't a public web page.

    The server does the fetching, so a URL is an instruction to make a request
    from inside wherever this is hosted. Without this, anyone who can reach the
    app can use it to probe localhost, the private network, or a cloud metadata
    endpoint — and read the result back as a lesson.
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


def fetch(url: str) -> tuple[str, str | None]:
    """Return (text, title). Raises BadUrl when there is nothing worth importing."""
    try:
        import trafilatura
    except ImportError as exc:  # pragma: no cover - a broken install, not a bad url
        raise BadUrl("URL import needs trafilatura: uv sync") from exc

    check(url)
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise BadUrl("could not fetch that page")

    text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
    if not text or not text.strip():
        raise BadUrl("no article text found on that page")

    meta = trafilatura.extract_metadata(downloaded)
    return text, (meta.title if meta else None)
