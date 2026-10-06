"""FastAPI application entrypoint.

Wires routers, CORS, security headers, rate limiting and startup seeding.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.routes import admin, auth, dataset, history, institute, predict, users
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.seed import init_db

configure_logging()
logger = get_logger("main")

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    init_db()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.middleware("http")
async def catch_unhandled_errors(request: Request, call_next):
    """Turn any unhandled error into a JSON 500 *inside* the CORS layer.

    FastAPI's Exception handler runs outside CORSMiddleware, so a crash
    returned a 500 without Access-Control-Allow-Origin and the browser only
    showed a misleading "blocked by CORS policy" / "Failed to fetch". Catching
    here (registered before CORS, so CORS wraps it) keeps the CORS headers on
    error responses and the real error is logged on Render.
    """
    try:
        return await call_next(request)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error. Please try again."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Basic hardening headers (XSS, clickjacking, sniffing)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get(f"{settings.API_PREFIX}/health", tags=["health"])
def health():
    # Also reports which cutoff data is live, so a deploy can be verified.
    from app.services.prediction_engine import dataset
    try:
        stats = dataset.stats()
        return {"status": "healthy", "dataset_rows": stats["valid_rows"], "dataset_loaded_at": stats["loaded_at"]}
    except Exception:
        return {"status": "healthy", "dataset_rows": None}


for r in (auth, users, admin, predict, history, dataset, institute):
    app.include_router(r.router, prefix=settings.API_PREFIX)
