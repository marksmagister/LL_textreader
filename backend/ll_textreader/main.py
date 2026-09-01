from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
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
