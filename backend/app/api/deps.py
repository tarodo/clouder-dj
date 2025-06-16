from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import oauth2_scheme, verify_token
from app.crud import crud_user
from app.db.models.user import User
from app.db.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    payload = verify_token(token)
    spotify_id: str | None = payload.get("sub")
    if spotify_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await crud_user.get_user_by_spotify_id(db, spotify_id=spotify_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
