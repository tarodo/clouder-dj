from __future__ import annotations

from typing import List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.core.settings import settings
from app.db.models.category import Category
from app.db.models.user import User
from app.repositories.category import CategoryRepository
from app.repositories.style import StyleRepository
from app.schemas.category import (
    CategoryCreate,
    CategoryCreateInternal,
    CategoryCreateResponse,
    CategoryUpdate,
    Category as CategorySchema,
)
from app.utils.transaction import transactional

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
        self.db: AsyncSession = category_repo.db

    async def get_categories_by_style(
        self, *, user_id: int, style_id: int
    ) -> List[CategorySchema]:
        categories = await self.category_repo.get_by_user_and_style(
            user_id=user_id, style_id=style_id
        )
        return [CategorySchema.model_validate(c) for c in categories]

    @transactional
    async def create_categories(
        self, *, categories_in: List[CategoryCreate], user: User, style_id: int
    ) -> List[CategoryCreateResponse]:
        """
        Creates categories in DB and corresponding playlists on Spotify.
        """
        style = await self.style_repo.get(id=style_id)
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
        created_spotify_playlists: List[dict] = []
        try:
            for cat_in in categories_in:
                playlist_name = settings.SPOTIFY_PLAYLIST_NAME_TEMPLATE.format(
                    style_name=style.name.upper(), category_name=cat_in.name.upper()
                )
                is_public = cat_in.is_public
                description = settings.SPOTIFY_PLAYLIST_DESCRIPTION_TEMPLATE.format(
                    playlist_name=playlist_name
                )

                log.info(
                    "Creating Spotify playlist",
                    playlist_name=playlist_name,
                    is_public=is_public,
                )
                playlist = await self.spotify_client.create_playlist(
                    name=playlist_name, public=is_public, description=description
                )
                created_spotify_playlists.append(playlist)

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
                "Spotify client failed during playlist creation. "
                "Rolling back DB and cleaning up created Spotify playlists.",
                exc_info=e,
            )
            # Cleanup created playlists on Spotify
            if created_spotify_playlists:
                log.info(
                    "Attempting to clean up orphaned Spotify playlists",
                    count=len(created_spotify_playlists),
                )
                for p in created_spotify_playlists:
                    try:
                        await self.spotify_client.unfollow_playlist(playlist_id=p["id"])
                    except SpotifyClientError as cleanup_exc:
                        log.error(
                            "Failed to clean up orphaned Spotify playlist",
                            playlist_id=p["id"],
                            playlist_name=p.get("name"),
                            exc_info=cleanup_exc,
                        )
            raise SpotifyPlaylistCreationError() from e

        return [CategoryCreateResponse.model_validate(c) for c in created_categories]

    @transactional
    async def update_category(
        self, *, category_id: int, category_in: CategoryUpdate, user_id: int
    ) -> CategorySchema | None:
        """
        Updates category metadata and optionally its corresponding Spotify playlist.
        """
        category = await self.category_repo.get(id=category_id)
        if not category or category.user_id != user_id:
            return None

        if category_in.name and category_in.name != category.name:
            # Check for name collision before updating
            existing = await self.category_repo.get_by_user_style_and_name(
                user_id=user_id, style_id=category.style_id, name=category_in.name
            )
            if existing and existing.id != category_id:
                raise CategoryAlreadyExistsError(category_name=category_in.name)

            style = await self.style_repo.get(id=category.style_id)
            if not style:
                # This should not happen if data is consistent
                raise StyleNotFoundError(category.style_id)

            new_playlist_name = settings.SPOTIFY_PLAYLIST_NAME_TEMPLATE.format(
                style_name=style.name.upper(), category_name=category_in.name.upper()
            )
            new_description = settings.SPOTIFY_PLAYLIST_DESCRIPTION_TEMPLATE.format(
                playlist_name=new_playlist_name
            )

            try:
                await self.spotify_client.update_playlist_details(
                    playlist_id=category.spotify_playlist_id,
                    name=new_playlist_name,
                    description=new_description,
                )
            except SpotifyNotFoundError:
                log.warning(
                    "Spotify playlist not found, deleting category from DB",
                    category_id=category_id,
                    spotify_playlist_id=category.spotify_playlist_id,
                )
                await self.category_repo.delete(id=category_id)
                return None

            updated_category = await self.category_repo.update(
                db_obj=category, obj_in=category_in
            )
            await self.db.refresh(updated_category)
            # Convert to Pydantic model while session is still active
            return CategorySchema.model_validate(updated_category)

        # Convert to Pydantic model while session is still active
        return CategorySchema.model_validate(category)

    @transactional
    async def delete_category(
        self, *, category_id: int, delete_on_spotify: bool, user_id: int
    ) -> CategorySchema | None:
        """Deletes a category from DB and optionally from Spotify."""
        category = await self.category_repo.get(id=category_id)
        if not category or category.user_id != user_id:
            return None

        if delete_on_spotify:
            await self.spotify_client.unfollow_playlist(
                playlist_id=category.spotify_playlist_id
            )

        deleted_category = await self.category_repo.delete(id=category_id)
        return (
            CategorySchema.model_validate(deleted_category)
            if deleted_category
            else None
        )
