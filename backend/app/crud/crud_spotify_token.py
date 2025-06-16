from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_data
from app.db.models.spotify_token import SpotifyToken
from app.db.models.user import User


async def create_or_update_token(
    db: AsyncSession, *, user: User, token_info: dict
) -> SpotifyToken:
    """
    Create or update Spotify tokens for a user.
    """
    result = await db.execute(
        select(SpotifyToken).filter(SpotifyToken.user_id == user.id)
    )
    db_token = result.scalars().first()

    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=token_info["expires_in"]
    )
    encrypted_access_token = encrypt_data(token_info["access_token"])

    if db_token:
        db_token.encrypted_access_token = encrypted_access_token
        if "refresh_token" in token_info and token_info["refresh_token"]:
            db_token.encrypted_refresh_token = encrypt_data(token_info["refresh_token"])
        db_token.expires_at = expires_at
        db_token.scope = token_info["scope"]
    else:
        if "refresh_token" not in token_info or not token_info["refresh_token"]:
            raise ValueError("Refresh token not found on initial authorization")

        db_token = SpotifyToken(
            user_id=user.id,
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=encrypt_data(token_info["refresh_token"]),
            expires_at=expires_at,
            scope=token_info["scope"],
        )
        db.add(db_token)

    # Committing here to be consistent with other CRUD functions in the project.
    await db.commit()
    await db.refresh(db_token)
    return db_token
