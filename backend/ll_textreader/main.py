from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import account, auth, dictionary, lessons, reports, terms, vocab
from .config import REPO_ROOT, settings
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


# No CORS middleware: nothing is ever cross-origin. Vite proxies /api in dev and
# this app serves the built frontend in production, so the browser only ever
# talks to one origin.
#
# There is no longer a shared password either. It was one door in front of one
# lexicon, and it made no sense once a request had to say *whose* lexicon it
# meant: every route that touches reader data now depends on `current_user`, and
# a request without a session gets a 401 from the route rather than from a
# middleware that could not tell the routes apart. Two doors would have been the
# kind of ceremony CLAUDE.md warns about — see docs/decisions/0021.
app = FastAPI(title="LL_textreader", version=__version__, lifespan=lifespan)

app.include_router(account.router)
app.include_router(auth.router)
app.include_router(dictionary.router)
app.include_router(lessons.router)
app.include_router(reports.router)
app.include_router(terms.router)
app.include_router(vocab.router)


@app.get("/api/health")
def health() -> dict[str, str | list[str]]:
    """Deliberately open. It says the version and which languages are loaded —
    nothing about any reader — and something has to answer before anyone signs in."""
    return {"status": "ok", "version": __version__, "languages": settings.language_list}


# Served from here rather than from the SPA for two reasons: Google's consent
# screen wants a URL it can fetch without running JavaScript, and somebody
# reading the privacy policy to decide whether to sign up must not have to sign
# up to read it. Registered before the static mount below, which would otherwise
# swallow both paths.
LEGAL = Path(__file__).parent / "legal"


def _page(name: str) -> HTMLResponse:
    style = (LEGAL / "_style.html").read_text(encoding="utf-8")
    return HTMLResponse(style + (LEGAL / name).read_text(encoding="utf-8"))


@app.get("/privacy", response_class=HTMLResponse)
def privacy() -> HTMLResponse:
    return _page("privacy.html")


@app.get("/terms", response_class=HTMLResponse)
def terms() -> HTMLResponse:
    return _page("terms.html")


# In production the built frontend is served from here, so a deployment is one
# container on one port. In dev this directory doesn't exist and Vite serves it.
DIST = REPO_ROOT / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
