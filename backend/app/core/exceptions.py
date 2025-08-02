import structlog
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Any

log = structlog.get_logger()


class BaseAPIException(Exception):
    status_code: int = 400
    code: str = "UNSPECIFIED_ERROR"
    detail: str = "An unspecified error occurred."

    def __init__(
        self,
        status_code: int | None = None,
        detail: str | None = None,
        code: str | None = None,
    ):
        if status_code is not None:
            self.status_code = status_code
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code
        super().__init__(self.detail)


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


class StyleNotFoundError(BaseAPIException):
    def __init__(self, style_id: int):
        super().__init__(
            status_code=404,  # Override status code to 404 Not Found
            code="STYLE_NOT_FOUND",
            detail=f"Style with id {style_id} not found.",
        )


class SpotifyPlaylistCreationError(BaseAPIException):
    code = "SPOTIFY_PLAYLIST_CREATION_FAILED"
    detail = "Failed to create the playlist on Spotify."


class CategoryCreationError(BaseAPIException):
    code = "CATEGORY_CREATION_FAILED"
    detail = "Failed to create one or more categories in the database."


class CategoryAlreadyExistsError(BaseAPIException):
    def __init__(self, category_name: str):
        super().__init__(
            status_code=409,
            code="CATEGORY_ALREADY_EXISTS",
            detail=f"Category '{category_name}' already exists for this style.",
        )


class RawLayerBlockExistsError(BaseAPIException):
    def __init__(self, block_name: str):
        super().__init__(
            status_code=409,
            code="RAW_LAYER_BLOCK_ALREADY_EXISTS",
            detail=f"Raw layer block '{block_name}' already exists for this style.",
        )
