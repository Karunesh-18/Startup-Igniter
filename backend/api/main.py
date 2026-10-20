"""
Startup OS — FastAPI application entry point.

This file wires together:
  - CORS middleware
  - All API routers
  - Startup/shutdown lifecycle hooks (DB engine, Redis pool)
  - Global exception handlers
  - OpenAPI customization

Run locally:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

Run in production (Fly.io / Render):
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
"""

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from api.routers import analysis, auth, export, forum, phases, projects, scores
from core.config import get_settings
from core.logging import configure_logging, get_logger

# ── Configure structured logging before anything else ─────────────────────────
configure_logging()
logger = get_logger(__name__)
settings = get_settings()


# ── Application lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager for application startup and shutdown.

    Startup:
      - Verify DB connection is reachable.
      - Log configuration summary.

    Shutdown:
      - Dispose DB connection pool.
      - Close Redis pool.
    """
    logger.info(
        "startup",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Warm up DB engine (validates DATABASE_URL on start)
    if settings.DATABASE_URL:
        try:
            from db.database import get_engine
            engine = get_engine()
            async with engine.connect() as conn:
                from sqlalchemy import text
                await conn.execute(text("SELECT 1"))
            logger.info("database_connected")
        except Exception as e:
            logger.warning("database_connection_failed", error=str(e))
    else:
        logger.warning("database_url_not_set_running_without_db")

    yield  # Application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────
    from db.database import close_db
    await close_db()
    logger.info("shutdown_complete")


# ── FastAPI application ───────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Startup OS — AI-Powered Startup Operating System

A phase-gated platform that guides founders from raw idea to validated startup plan,
business documents, and legal checklists.

### Key features:
- **Idea Analysis** — AI categorization and problem-solution fit analysis
- **Validation** — Market research, competitor analysis, SWOT, readiness score
- **Business Planning** — Lean Canvas generation from cross-phase memory
- **Document Export** — PDF, DOCX, PPTX generation
- **Community Forum** — Discussion board for founders

### Authentication:
All endpoints (except health) require a Bearer JWT token.
Obtain one via `POST /auth/register` or `POST /auth/login`.

### AI Guardrails:
All AI-generated content is flagged with `ai_generated: true`.
Frontend MUST display: *"AI-generated — verify independently."*
Legal documents always show: *"Have a qualified lawyer review before use."*
""",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["http://localhost:5173", "http://localhost:3000"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

if settings.is_production:
    # In production, only accept requests from known hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.fly.dev", "*.render.com", "*.vercel.app", "localhost"],
    )


# ── Request ID + timing middleware ────────────────────────────────────────────

@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    """
    Inject a request ID header and log response time.
    Useful for correlating logs in production.
    """
    import uuid as _uuid
    request_id = str(_uuid.uuid4())
    start = time.perf_counter()

    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
        request_id=request_id,
    )
    return response


# ── Global exception handlers ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions — return 500 without leaking internals."""
    logger.exception(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "type": "internal_error",
        },
    )


# ── Health check ──────────────────────────────────────────────────────────────

@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    response_model=dict[str, Any],
)
async def health_check() -> dict[str, Any]:
    """
    Simple liveness probe for Fly.io / Render health checks.

    Returns:
        {"status": "ok", "version": "...", "environment": "..."}
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ── Routers ───────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(phases.router, prefix=API_PREFIX)
app.include_router(scores.router, prefix=API_PREFIX)
app.include_router(forum.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)
app.include_router(analysis.router, prefix=API_PREFIX)


# ── Root redirect ─────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")
