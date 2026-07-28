# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# System dependencies for weasyprint and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libffi-dev \
    libssl-dev \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libgdk-pixbuf2.0-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dependencies ──────────────────────────────────────────────────────────────
FROM base AS deps

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# ── Application ───────────────────────────────────────────────────────────────
FROM deps AS app

COPY . .

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# ── Worker (arq) ─────────────────────────────────────────────────────────────
FROM deps AS worker

COPY . .
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["arq", "workers.tasks.WorkerSettings"]
