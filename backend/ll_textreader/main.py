from base64 import b64encode
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from secrets import compare_digest

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import dictionary, lessons, terms, vocab
from .config import REPO_ROOT, settings
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="LL_textreader", version=__version__, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_password(request: Request, call_next):
    """One shared password over HTTP basic auth.

    This is a single-user app: there are no accounts, and whoever gets in reads
    with the one lexicon. The password is not a login system, it is a door — but
    a tunnel or a public host makes it the only thing between your reading
    history and anyone who guesses the URL.
    """
    if settings.password:
        header = request.headers.get("authorization", "")
        expected = b64encode(f"{settings.username}:{settings.password}".encode()).decode()
        scheme, _, given = header.partition(" ")
        # compare_digest, so the answer doesn't leak through response timing
        if scheme.lower() != "basic" or not compare_digest(given, expected):
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="LL_textreader"'},
            )
    return await call_next(request)


app.include_router(dictionary.router)
app.include_router(lessons.router)
app.include_router(terms.router)
app.include_router(vocab.router)


@app.get("/api/health")
def health() -> dict[str, str | list[str]]:
    return {"status": "ok", "version": __version__, "languages": settings.language_list}


# In production the built frontend is served from here, so a deployment is one
# container on one port. In dev this directory doesn't exist and Vite serves it.
DIST = REPO_ROOT / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
