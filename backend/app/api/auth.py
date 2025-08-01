from secrets import token_urlsafe
from urllib.parse import urlencode

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.deps import get_auth_service
from app.core import security
from app.core.settings import settings
from app.schemas.auth import TokenRefreshRequest, TokenRefreshResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
log = structlog.get_logger()


@router.get("/login")
async def login():
    """
    Initiates the Spotify OAuth2 login flow.
    """
    log.info("Initiating Spotify login flow")
    # Generate state and PKCE challenge
    state = token_urlsafe(32)
    code_verifier, code_challenge = security.create_pkce_challenge()

    # Build authorization URL
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
        "state": state,
        "scope": settings.SPOTIFY_SCOPES,
    }
    auth_url = f"{settings.SPOTIFY_AUTH_URL}?{urlencode(params)}"

    # Create response with cookies
    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key="spotify_auth_state",
        value=state,
        httponly=True,
        max_age=600,
        secure=settings.SECURE_COOKIES,
    )
    response.set_cookie(
        key="spotify_code_verifier",
        value=code_verifier,
        httponly=True,
        max_age=600,
        secure=settings.SECURE_COOKIES,
    )

    return response


@router.get("/callback")
async def callback(
    code: str,
    state: str,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Exchanges the authorization code for an access token and fetches user profile.
    """
    log.info("Handling Spotify callback")
    # Verify state matches
    if (
        not (stored_state := request.cookies.get("spotify_auth_state"))
        or state != stored_state
    ):
        log.warning(
            "State mismatch during Spotify callback",
            received_state=state,
            stored_state=stored_state,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State mismatch",
        )

    # Get code verifier from cookies
    if not (code_verifier := request.cookies.get("spotify_code_verifier")):
        log.warning("Code verifier not found in cookies")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code verifier not found",
        )

    tokens = await auth_service.handle_spotify_callback(
        code=code, code_verifier=code_verifier
    )
    response = JSONResponse(content=tokens)
    response.delete_cookie("spotify_auth_state")
    response.delete_cookie("spotify_code_verifier")

    return response


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(request: TokenRefreshRequest):
    """
    Refreshes the application access token using a valid refresh token.
    """
    payload = security.verify_token(request.refresh_token)
    spotify_id: str | None = payload.get("sub")
    if not spotify_id:
        log.warning("Could not validate credentials, 'sub' not in token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = security.create_access_token(data={"sub": spotify_id})
    return TokenRefreshResponse(access_token=new_access_token)
