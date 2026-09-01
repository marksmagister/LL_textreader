from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api import dictionary, lessons, terms
from .config import settings
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


@app.get("/api/health")
def health() -> dict[str, str | list[str]]:
    return {"status": "ok", "version": __version__, "languages": settings.language_list}
