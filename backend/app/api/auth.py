import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
    create_pkce_challenge,
    create_refresh_token,
)
from app.core.settings import settings
from app.crud import crud_user
from app.schemas.user import UserCreate, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


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
        "scope": settings.SPOTIFY_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    spotify_auth_url = f"{settings.SPOTIFY_AUTH_URL}?{urlencode(query_params)}"

    response = RedirectResponse(url=spotify_auth_url)
    response.set_cookie(
        key="spotify_auth_state", value=state, httponly=True, samesite="lax"
    )
    response.set_cookie(
        key="spotify_code_verifier", value=code_verifier, httponly=True, samesite="lax"
    )
    return response


@router.get("/callback")
async def callback(
    request: Request, code: str, state: str, db: AsyncSession = Depends(get_db)
):
    """
    Handles the callback from Spotify after user authentication.
    Exchanges the authorization code for an access token and fetches user profile.
    """
    # Verify state matches
    stored_state = request.cookies.get("spotify_auth_state")
    if not stored_state or state != stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State mismatch",
        )

    # Get code verifier from cookies
    code_verifier = request.cookies.get("spotify_code_verifier")
    if not code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code verifier not found",
        )

    # Exchange code for access token
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"{settings.BASE_URL}/auth/callback",
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "code_verifier": code_verifier,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(settings.SPOTIFY_TOKEN_URL, data=token_data)
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token",
            )
        token_info = token_response.json()

        # Get user profile
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}
        profile_response = await client.get(settings.SPOTIFY_API_URL, headers=headers)
        if profile_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user profile",
            )
        user_profile = profile_response.json()

    # Save/update user in DB
    user = await crud_user.get_user_by_spotify_id(db, spotify_id=user_profile["id"])
    if user:
        user_in_update = UserUpdate(
            display_name=user_profile.get("display_name"),
            email=user_profile.get("email"),
        )
        await crud_user.update_user(db=db, db_obj=user, obj_in=user_in_update)
    else:
        user_in_create = UserCreate(
            spotify_id=user_profile["id"],
            display_name=user_profile.get("display_name"),
            email=user_profile.get("email"),
        )
        await crud_user.create_user(db=db, obj_in=user_in_create)

    spotify_id = user_profile["id"]

    access_token = create_access_token(data={"sub": spotify_id})
    refresh_token = create_refresh_token(data={"sub": spotify_id})

    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

    response = JSONResponse(content=response_data)
    response.delete_cookie(key="spotify_auth_state")
    response.delete_cookie(key="spotify_code_verifier")
    return response
