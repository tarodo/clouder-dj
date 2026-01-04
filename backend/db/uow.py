from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import AsyncSessionLocal
from backend.repositories.integration import IntegrationRepository
from backend.repositories.label import LabelRepository
from backend.repositories.release import ReleaseRepository
from backend.repositories.user import UserRepository


class UnitOfWork:
    def __init__(self) -> None:
        self.session_factory = AsyncSessionLocal

    async def __aenter__(self) -> UnitOfWork:
        self.session: AsyncSession = self.session_factory()
        self.users = UserRepository(self.session)
        self.integrations = IntegrationRepository(self.session)
        self.labels = LabelRepository(self.session)
        self.releases = ReleaseRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
