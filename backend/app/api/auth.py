import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.security import (
    create_access_token,
    create_pkce_challenge,
    create_refresh_token,
)
from app.core.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"  # noqa: S105
SPOTIFY_API_URL = "https://api.spotify.com/v1/me"
SCOPES = "user-read-private user-read-email"


@router.get("/login")
def login():
    """
    Redirects the user to Spotify for authentication.
    Generates and stores PKCE code verifier and state in cookies.
    """
    state = secrets.token_urlsafe(16)
    code_verifier, code_challenge = create_pkce_challenge()

    query_params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": f"{settings.BASE_URL}/auth/callback",
        "scope": SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    spotify_auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(query_params)}"

    response = RedirectResponse(url=spotify_auth_url)
    response.set_cookie(
        key="spotify_auth_state", value=state, httponly=True, samesite="lax"
    )
    response.set_cookie(
        key="spotify_code_verifier", value=code_verifier, httponly=True, samesite="lax"
    )
    return response


@router.get("/callback")
async def callback(request: Request, code: str, state: str):
    """
    Handles the callback from Spotify after user authentication.
    Exchanges the authorization code for an access token and fetches user profile.
    Returns JWT and user profile.
    """
    stored_state = request.cookies.get("spotify_auth_state")
    code_verifier = request.cookies.get("spotify_code_verifier")

    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="State mismatch"
        )
    if not code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Code verifier not found"
        )

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"{settings.BASE_URL}/auth/callback",
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "code_verifier": code_verifier,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            SPOTIFY_TOKEN_URL,
            data=token_data,
            auth=(
                settings.SPOTIFY_CLIENT_ID,
                settings.SPOTIFY_CLIENT_SECRET,
            ),
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve token from Spotify: {token_response.text}",
            )
        spotify_tokens = token_response.json()

        headers = {"Authorization": f"Bearer {spotify_tokens['access_token']}"}
        profile_response = await client.get(SPOTIFY_API_URL, headers=headers)

        if profile_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve user profile from Spotify: {profile_response.text}",  # noqa: E501
            )
        user_profile = profile_response.json()

    user_id = user_profile["id"]
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})

    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_profile": user_profile,
    }

    response = JSONResponse(content=response_data)
    response.delete_cookie("spotify_auth_state")
    response.delete_cookie("spotify_code_verifier")

    return response
