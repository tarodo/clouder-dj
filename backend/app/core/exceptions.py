import structlog
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Any

log = structlog.get_logger()


async def http_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, StarletteHTTPException):
        log.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=str(request.url),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    raise exc


async def validation_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, RequestValidationError):
        log.warning(
            "Validation exception",
            errors=exc.errors(),
            path=str(request.url),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({"detail": exc.errors()}),
        )
    raise exc


async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Handler for unhandled exceptions, to ensure they are logged.
    """
    log.exception("Unhandled exception", path=str(request.url))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )


API_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Bad Request",
        "content": {"application/json": {"example": {"detail": "Bad Request"}}},
    },
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {"detail": "Could not validate credentials"}
            }
        },
    },
    404: {
        "description": "Not Found",
        "content": {"application/json": {"example": {"detail": "Not Found"}}},
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {"example": {"detail": "Internal Server Error"}}
        },
    },
}
