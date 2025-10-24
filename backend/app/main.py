import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import (
    artists,
    auth,
    category,
    collection,
    labels,
    me,
    release_playlists,
    releases,
    styles,
    tasks,
    tracks,
    raw_layer,
)
from app.broker import broker
from app.core.exceptions import (
    API_RESPONSES,
    BaseAPIException,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.core.settings import settings
from app.schemas.error import ErrorResponse

# Import tasks to register them

setup_logging()

log = structlog.get_logger()


async def api_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, BaseAPIException):
        raise exc

    request_id = structlog.contextvars.get_contextvars().get("request_id", "N/A")
    log.warning(
        "API Error Handled",
        error_code=exc.code,
        error_detail=exc.detail,
        status_code=exc.status_code,
        path=str(request.url),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.code,
            detail=exc.detail,
            request_id=request_id,
        ).model_dump(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting up Clouder-DJ API", base_url=settings.BASE_URL)
    if not broker.is_worker_process:
        await broker.startup()
    yield
    log.info("Shutting down Clouder-DJ API")
    if not broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(
    title="Clouder-DJ API",
    version="0.1.0",
    description="API for Clouder-DJ, a collaborative music queueing service.",
    responses=API_RESPONSES,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With", "X-Request-ID"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start_time = time.perf_counter()
    log.info(
        "Request started",
        http_method=request.method,
        http_path=request.url.path,
        client_host=request.client.host if request.client else None,
    )

    response = await call_next(request)

    process_time = time.perf_counter() - start_time
    log.info(
        "Request finished",
        status_code=response.status_code,
        process_time=round(process_time, 4),
    )
    # Ensure response carries the correlation id
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(auth.router)
app.include_router(me.router)
app.include_router(artists.router)
app.include_router(labels.router)
app.include_router(releases.router)
app.include_router(tracks.router)
app.include_router(styles.router)
app.include_router(collection.router)
app.include_router(tasks.router)
app.include_router(category.router)
app.include_router(raw_layer.router)
app.include_router(release_playlists.router)

app.add_exception_handler(BaseAPIException, api_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
