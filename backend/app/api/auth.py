from secrets import token_urlsafe
from urllib.parse import urlencode

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.api.deps import get_spotify_api_client, get_uow
from app.clients.spotify import SpotifyAPIClient
from app.core import security
from app.core.settings import settings
from app.db.uow import AbstractUnitOfWork
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
    uow: AbstractUnitOfWork = Depends(get_uow),
    spotify_client: SpotifyAPIClient = Depends(get_spotify_api_client),
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

    auth_service = AuthService(db=uow.session, spotify_client=spotify_client)
    tokens = await auth_service.handle_spotify_callback(
        code=code, code_verifier=code_verifier
    )

    params = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "spotify_access_token": tokens["spotify_access_token"],
    }
    redirect_url = f"{settings.FRONTEND_URL}/spotify-callback?{urlencode(params)}"
    response = RedirectResponse(url=redirect_url)
    response.delete_cookie("spotify_auth_state")
    response.delete_cookie("spotify_code_verifier")

    return response


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    uow: AbstractUnitOfWork = Depends(get_uow),
    spotify_client: SpotifyAPIClient = Depends(get_spotify_api_client),
):
    """
    Refreshes the application access token and the Spotify access token.
    """
    auth_service = AuthService(db=uow.session, spotify_client=spotify_client)
    return await auth_service.refresh_app_and_spotify_tokens(request.refresh_token)
