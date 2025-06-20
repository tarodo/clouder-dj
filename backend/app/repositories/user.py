from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=User, db=db)

    async def get_by_spotify_id(self, *, spotify_id: str) -> User | None:
        result = await self.db.execute(
            select(User).filter(User.spotify_id == spotify_id)
        )
        return result.scalars().first()

    async def create(self, *, obj_in: UserCreate) -> User:
        db_obj = User(
            spotify_id=obj_in.spotify_id,
            display_name=obj_in.display_name,
            email=obj_in.email,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, *, db_obj: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
