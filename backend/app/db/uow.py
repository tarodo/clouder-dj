from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories import (
    ArtistRepository,
    CategoryRepository,
    ExternalDataRepository,
    LabelRepository,
    RawLayerRepository,
    ReleaseRepository,
    SpotifyTokenRepository,
    StyleRepository,
    TrackRepository,
    UserRepository,
)


class AbstractUnitOfWork(ABC):
    artists: ArtistRepository
    categories: CategoryRepository
    external_data: ExternalDataRepository
    labels: LabelRepository
    raw_layer: RawLayerRepository
    releases: ReleaseRepository
    spotify_tokens: SpotifyTokenRepository
    styles: StyleRepository
    tracks: TrackRepository
    users: UserRepository
    session: AsyncSession

    @abstractmethod
    async def __aenter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session = self._session_factory()
        self.artists = ArtistRepository(self.session)
        self.categories = CategoryRepository(self.session)
        self.external_data = ExternalDataRepository(self.session)
        self.labels = LabelRepository(self.session)
        self.raw_layer = RawLayerRepository(self.session)
        self.releases = ReleaseRepository(self.session)
        self.spotify_tokens = SpotifyTokenRepository(self.session)
        self.styles = StyleRepository(self.session)
        self.tracks = TrackRepository(self.session)
        self.users = UserRepository(self.session)
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
