import os
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from http import HTTPStatus

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from hawk_python_sdk import Hawk
from prometheus_client import CollectorRegistry, make_asgi_app, multiprocess
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.responses import Response

from app.api.v1 import auth, comments, news, users
from app.core.config import settings
from app.core.logger import configure_logger
from app.db.cache import close_redis_pool, init_redis_pool

# --- ОБЩАЯ НАСТРОЙКА ---
configure_logger()
logger = structlog.get_logger()


# --- LIFESPAN ДЛЯ STARTUP/SHUTDOWN ---
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Действия при старте
    prometheus_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if prometheus_dir:
        os.makedirs(prometheus_dir, exist_ok=True)  # noqa: PTH103

    # Инициализация Hawk
    if settings.HAWK_TOKEN and settings.HAWK_TOKEN != "your_hawk_token_here":  # noqa: S105
        try:
            _app.state.hawk_client = Hawk(settings.HAWK_TOKEN)
        except Exception:  # noqa: BLE001
            _app.state.hawk_client = None
    else:
        _app.state.hawk_client = None

    await init_redis_pool()
    yield
    # Действия при остановке
    await close_redis_pool()


app = FastAPI(title="news-api-backend", lifespan=lifespan)
app.state.hawk_client = None


# --- MIDDLEWARES ---


# Middleware для Hawk
@app.middleware("http")
async def hawk_exception_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    try:
        return await call_next(request)
    except Exception as e:
        hawk_client = request.app.state.hawk_client

        if hawk_client:
            try:
                hawk_client.send(e)
            except Exception as hawk_e:
                logger.exception("Failed to send error to Hawk", error=str(hawk_e))

        raise


# Middleware для Structlog
@app.middleware("http")
async def structlog_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID", "unknown")
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
    )

    start_time = time.perf_counter_ns()

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception("Request failed", error=str(e))
        raise
    else:
        process_time = time.perf_counter_ns() - start_time

        structlog.contextvars.bind_contextvars(
            status_code=response.status_code,
            process_time=process_time / 10**6,  # ms
        )

        if HTTPStatus.BAD_REQUEST <= response.status_code < HTTPStatus.INTERNAL_SERVER_ERROR:
            logger.warning("Client error")
        elif response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
            logger.error("Server error")
        else:
            logger.info("Request processed")

        return response


# Middleware для CORS
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- PROMETHEUS METRICS ---
Instrumentator().instrument(app)
registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)
metrics_app = make_asgi_app(registry=registry)
app.mount("/metrics", metrics_app)


# --- ROUTERS ---
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(news.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")


# --- ТЕСТОВЫЕ РУЧКИ ---
@app.get("/")
def read_root() -> dict[str, str]:
    logger.info("Root endpoint called")
    return {"message": "Welcome to the news API"}


@app.get("/error_test", response_model=None)
def trigger_error() -> None:
    """Тестовая ручка для проверки Hawk."""
    msg = "This is a test error for Hawk!"
    raise ValueError(msg)
