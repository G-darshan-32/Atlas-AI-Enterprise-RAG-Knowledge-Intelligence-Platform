import time
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.redis import close_redis
from app.api.v1 import api_router

# ─── Structlog configuration ─────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.JSONRenderer() if settings.APP_ENV == "production"
        else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("atlas_ai_starting", version=settings.APP_VERSION, env=settings.APP_ENV)

    # Verify Redis
    try:
        from app.core.redis import get_redis
        redis = await get_redis()
        await redis.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.warning("redis_unavailable", error=str(e))

    # Ensure MinIO bucket exists
    try:
        from app.services.storage_service import StorageService
        await StorageService().ensure_bucket()
        logger.info("storage_ready", bucket=settings.S3_BUCKET_NAME)
    except Exception as e:
        logger.warning("storage_unavailable", error=str(e))

    yield

    await close_redis()
    logger.info("atlas_ai_shutdown")


# ─── App factory ─────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Workspace for Organizational Intelligence — REST API",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list)
                  else [settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.APP_ENV == "production":
    # Restrict to the configured frontend domain; falls back to localhost for safety
    _allowed_hosts = [settings.FRONTEND_URL.split("//")[-1].split("/")[0]] if settings.FRONTEND_URL else ["localhost"]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    """Log every request with timing."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = int((time.perf_counter() - start) * 1000)

    # Skip logging for health checks to reduce noise
    if request.url.path != "/health":
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
            ip=request.client.host if request.client else "unknown",
        )

    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response


# ─── Exception handlers ──────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ─── Health & Metrics ────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION, "env": settings.APP_ENV}


@app.get("/health/detailed", tags=["Health"])
async def health_detailed():
    """Deep health check — tests Redis and DB connectivity."""
    checks = {"api": "ok", "redis": "unknown", "database": "unknown"}

    try:
        from app.core.redis import get_redis
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    try:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await db.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "healthy" if all_ok else "degraded", "checks": checks},
    )


@app.get("/metrics", tags=["Health"])
async def prometheus_metrics():
    """Basic Prometheus-compatible metrics endpoint."""
    from app.core.redis import get_redis
    try:
        redis = await get_redis()
        info = await redis.info("server")
        uptime = info.get("uptime_in_seconds", 0)
    except Exception:
        uptime = 0

    lines = [
        "# HELP atlas_api_up API server uptime indicator",
        "# TYPE atlas_api_up gauge",
        f"atlas_api_up 1",
        f"atlas_redis_uptime_seconds {uptime}",
    ]
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


# ─── Routes ──────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.DEBUG)
