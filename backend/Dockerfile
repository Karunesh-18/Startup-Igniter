# Build with the REPO ROOT as context (not `backend/`):
#   docker build -f backend/Dockerfile .
# docker-compose.yml already does this (context: ..). This is required because
# `backend/` imports the sibling `ai/` package at the repo root (see
# backend/core/config.py's sys.path bootstrap) -- a build context scoped to
# `backend/` cannot COPY files that live outside it, so `ai/` was previously
# silently absent from the image and the API would fail at import time.

# -- Base image ----------------------------------------------------------------
FROM python:3.11-slim AS base

# System dependencies for weasyprint and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends     libpango-1.0-0     libpangoft2-1.0-0     libffi-dev     libssl-dev     libcairo2     libgdk-pixbuf-2.0-0     libgdk-pixbuf2.0-dev     shared-mime-info     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# -- Dependencies ----------------------------------------------------------------
FROM base AS deps

COPY backend/pyproject.toml backend/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir -e ./backend

# -- Application -------------------------------------------------------------
FROM deps AS app

COPY ai/ ./ai/
COPY backend/ ./backend/

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# -- Worker (arq) --------------------------------------------------------------
FROM deps AS worker

COPY ai/ ./ai/
COPY backend/ ./backend/
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/backend
CMD ["arq", "workers.tasks.WorkerSettings"]
