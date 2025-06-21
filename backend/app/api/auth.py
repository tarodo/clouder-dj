from secrets import token_urlsafe
from urllib.parse import urlencode

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.clients.spotify import SpotifyAPIClient
from app.core.security import create_pkce_challenge
from app.core.settings import settings
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
    code_verifier, code_challenge = create_pkce_challenge()

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
    db: AsyncSession = Depends(get_db),
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

    async with httpx.AsyncClient() as http_client:
        spotify_client = SpotifyAPIClient(client=http_client)
        auth_service = AuthService(db=db, spotify_client=spotify_client)
        tokens = await auth_service.handle_spotify_callback(
            code=code, code_verifier=code_verifier
        )

    response = JSONResponse(content=tokens)
    response.delete_cookie("spotify_auth_state")
    response.delete_cookie("spotify_code_verifier")

    return response
