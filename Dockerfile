# One container: the API and the built frontend on one port. Deployment is
# `git pull` + `docker compose up -d --build` (see docs/deploying.md).

FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app

# Dependencies first, so a code change doesn't refetch spaCy.
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY backend/ll_textreader/__init__.py backend/ll_textreader/
RUN uv sync --frozen --extra nlp --no-dev

# The model is not vendored (see NOTICE); it is fetched at build time.
RUN uv run python -m spacy download fr_core_news_md

COPY backend/ backend/
COPY --from=frontend /app/frontend/dist frontend/dist

ENV LL_TEXTREADER_DB_PATH=/data/ll_textreader.db \
    LL_TEXTREADER_DATA_DIR=/data
VOLUME /data
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "ll_textreader.main:app", \
     "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
