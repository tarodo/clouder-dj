from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.repositories.user import UserRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def get_user_by_spotify_id(self, spotify_id: str) -> User | None:
        return await self.user_repo.get_by_spotify_id(spotify_id=spotify_id)
