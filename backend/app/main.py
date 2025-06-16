from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth, me
from app.core.exceptions import (
    API_RESPONSES,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.settings import settings

app = FastAPI(
    title="Clouder-DJ API",
    version="0.1.0",
    description="API for Clouder-DJ, a collaborative music queueing service.",
    responses=API_RESPONSES,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(me.router)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
