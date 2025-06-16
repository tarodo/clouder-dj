from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_user_by_spotify_id(db: AsyncSession, *, spotify_id: str) -> User | None:
    result = await db.execute(select(User).filter(User.spotify_id == spotify_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, *, obj_in: UserCreate) -> User:
    db_obj = User(
        spotify_id=obj_in.spotify_id,
        display_name=obj_in.display_name,
        email=obj_in.email,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_user(db: AsyncSession, *, db_obj: User, obj_in: UserUpdate) -> User:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
