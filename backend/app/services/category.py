from __future__ import annotations

from typing import List

import structlog

from app.clients.spotify import (
    SpotifyClientError,
    SpotifyNotFoundError,
    UserSpotifyClient,
)
from app.core.exceptions import (
    CategoryAlreadyExistsError,
    SpotifyPlaylistCreationError,
    StyleNotFoundError,
)
from app.db.models.category import Category
from app.db.models.user import User
from app.repositories.category import CategoryRepository
from app.repositories.style import StyleRepository
from app.schemas.category import CategoryCreate, CategoryCreateInternal, CategoryUpdate

log = structlog.get_logger()


class CategoryService:
    def __init__(
        self,
        category_repo: CategoryRepository,
        style_repo: StyleRepository,
        user_spotify_client: UserSpotifyClient,
    ):
        self.category_repo = category_repo
        self.style_repo = style_repo
        self.spotify_client = user_spotify_client

    async def get_categories_by_style(
        self, *, user_id: int, style_id: int
    ) -> List[Category]:
        return await self.category_repo.get_by_user_and_style(
            user_id=user_id, style_id=style_id
        )

    async def create_categories(
        self, *, categories_in: List[CategoryCreate], user: User, style_id: int
    ) -> List[Category]:
        """
        Creates categories in DB and corresponding playlists on Spotify.
        This is a transactional operation. A failure in any Spotify API call
        will result in a rollback of all DB changes for this operation.
        """
        # Get style name for playlist formatting
        style = await self.style_repo.get(id=style_id)
        log.info("Style", style=style)
        if not style:
            raise StyleNotFoundError(style_id=style_id)

        # Check for existing categories before creating any playlists
        for cat_in in categories_in:
            existing_category = await self.category_repo.get_by_user_style_and_name(
                user_id=user.id, style_id=style_id, name=cat_in.name
            )
            if existing_category:
                raise CategoryAlreadyExistsError(category_name=cat_in.name)

        created_categories: List[Category] = []
        try:
            for cat_in in categories_in:
                playlist_name = f"{style.name.upper()} :: {cat_in.name.upper()}"
                is_public = cat_in.is_public
                description = f"Clouder-DJ: {playlist_name} category playlist."

                log.info(
                    "Creating Spotify playlist",
                    playlist_name=playlist_name,
                    is_public=is_public,
                )
                playlist = await self.spotify_client.create_playlist(
                    name=playlist_name, public=is_public, description=description
                )

                category_create_schema = CategoryCreateInternal(
                    name=cat_in.name,
                    user_id=user.id,
                    style_id=style_id,
                    spotify_playlist_id=playlist["id"],
                    spotify_playlist_url=playlist["external_urls"]["spotify"],
                )
                category = await self.category_repo.create(
                    obj_in=category_create_schema
                )
                created_categories.append(category)

        except SpotifyClientError as e:
            log.error(
                "Spotify client failed during playlist creation, "
                "transaction will be rolled back.",
                exc_info=e,
            )
            raise SpotifyPlaylistCreationError() from e

        return created_categories

    async def update_category(
        self, *, category_id: int, category_in: CategoryUpdate, user_id: int
    ) -> Category | None:
        """
        Updates a category name in DB and on Spotify.
        If the playlist is not found on Spotify, it deletes the local category.
        """
        category = await self.category_repo.get(id=category_id)
        if not category or category.user_id != user_id:
            return None

        if category_in.name:
            try:
                await self.spotify_client.update_playlist_details(
                    playlist_id=category.spotify_playlist_id, name=category_in.name
                )
            except SpotifyNotFoundError:
                log.warning(
                    "Playlist not found on Spotify during update. Deleting category.",
                    playlist_id=category.spotify_playlist_id,
                    category_id=category_id,
                )
                await self.category_repo.delete(id=category_id)
                return None

        return await self.category_repo.update(db_obj=category, obj_in=category_in)

    async def delete_category(
        self, *, category_id: int, delete_on_spotify: bool, user_id: int
    ) -> Category | None:
        """Deletes a category from DB and optionally from Spotify."""
        category = await self.category_repo.get(id=category_id)
        if not category or category.user_id != user_id:
            return None

        if delete_on_spotify:
            await self.spotify_client.unfollow_playlist(
                playlist_id=category.spotify_playlist_id
            )

        return await self.category_repo.delete(id=category_id)
