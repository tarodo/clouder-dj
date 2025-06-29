from __future__ import annotations

from typing import List

import structlog

from app.clients.spotify import SpotifyNotFoundError, UserSpotifyClient
from app.db.models.category import Category
from app.db.models.user import User
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate

log = structlog.get_logger()


class CategoryService:
    def __init__(
        self,
        category_repo: CategoryRepository,
        user_spotify_client: UserSpotifyClient,
    ):
        self.category_repo = category_repo
        self.spotify_client = user_spotify_client

    async def create_categories(
        self, *, categories_in: List[dict], user: User, style_id: int
    ) -> List[Category]:
        """
        Creates categories in DB and corresponding playlists on Spotify.
        This is a transactional operation. A failure in any Spotify API call
        will result in a rollback of all DB changes for this operation.
        """
        created_categories: List[Category] = []
        try:
            for cat_in in categories_in:
                playlist_name = cat_in["name"]
                is_public = cat_in.get("is_public", False)
                description = f"Clouder-DJ: {playlist_name} category playlist."

                log.info(
                    "Creating Spotify playlist",
                    name=playlist_name,
                    user_id=user.id,
                )
                playlist = await self.spotify_client.create_playlist(
                    name=playlist_name, public=is_public, description=description
                )

                category_create_schema = CategoryCreate(
                    name=playlist_name,
                    user_id=user.id,
                    style_id=style_id,
                    spotify_playlist_id=playlist["id"],
                    spotify_playlist_url=playlist["external_urls"]["spotify"],
                )
                category = await self.category_repo.create(
                    obj_in=category_create_schema
                )
                created_categories.append(category)

        except Exception:
            log.exception(
                "Failed to create categories, transaction will be rolled back."
            )
            raise  # Re-raise to trigger rollback in the calling context

        return created_categories

    async def update_category(
        self, *, category_id: int, category_in: CategoryUpdate
    ) -> Category | None:
        """
        Updates a category name in DB and on Spotify.
        If the playlist is not found on Spotify, it deletes the local category.
        """
        category = await self.category_repo.get(id=category_id)
        if not category:
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
        self, *, category_id: int, delete_on_spotify: bool
    ) -> Category | None:
        """Deletes a category from DB and optionally from Spotify."""
        category = await self.category_repo.get(id=category_id)
        if not category:
            return None

        if delete_on_spotify:
            await self.spotify_client.unfollow_playlist(
                playlist_id=category.spotify_playlist_id
            )

        return await self.category_repo.delete(id=category_id)
