import time
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth, me
from app.core.exceptions import (
    API_RESPONSES,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.core.settings import settings

setup_logging()

log = structlog.get_logger()

app = FastAPI(
    title="Clouder-DJ API",
    version="0.1.0",
    description="API for Clouder-DJ, a collaborative music queueing service.",
    responses=API_RESPONSES,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return response


app.include_router(auth.router)
app.include_router(me.router)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.on_event("startup")
async def startup_event():
    log.info("Starting Clouder-DJ API", base_url=settings.BASE_URL)


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
