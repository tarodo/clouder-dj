from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    get_category_service,
    get_current_user,
    get_uow,
    get_user_spotify_client,
)
from app.clients.spotify import UserSpotifyClient
from app.db.models.user import User
from app.db.uow import AbstractUnitOfWork
from app.schemas.category import (
    Category,
    CategoryCreate,
    CategoryCreateResponse,
    CategoryTrackAdd,
    CategoryUpdate,
    CategoryWithStyle,
)
from app.services.category import CategoryService

router = APIRouter(prefix="/curation", tags=["curation"])


@router.post(
    "/styles/{style_id}/categories",
    response_model=List[CategoryCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_categories(
    style_id: int,
    categories_in: List[CategoryCreate],
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_uow),
    user_spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
):
    """
    Creates one or more new categories for the current user and a given style.
    This is a transactional operation that creates both a Spotify playlist
    and a database record for each category.
    """
    category_service = CategoryService(
        category_repo=uow.categories,
        style_repo=uow.styles,
        user_spotify_client=user_spotify_client,
    )
    created_categories = await category_service.create_categories(
        categories_in=categories_in, user=current_user, style_id=style_id
    )
    return created_categories


@router.get("/categories", response_model=List[CategoryWithStyle])
async def get_all_categories(
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    Lists all categories for the current user with style information.
    """
    categories = await category_service.get_all_categories_for_user(
        user_id=current_user.id
    )
    return [
        CategoryWithStyle(
            **{k: v for k, v in c.__dict__.items() if not k.startswith("_")},
            style_name=c.style.name,
        )
        for c in categories
    ]


@router.get("/styles/{style_id}/categories", response_model=List[Category])
async def get_categories(
    style_id: int,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    Lists all categories for the current user and a given style.
    """
    return await category_service.get_categories_by_style(
        user_id=current_user.id, style_id=style_id
    )


@router.patch("/categories/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_uow),
    user_spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
):
    """
    Updates the name of a category and its corresponding Spotify playlist.
    """
    category_service = CategoryService(
        category_repo=uow.categories,
        style_repo=uow.styles,
        user_spotify_client=user_spotify_client,
    )
    updated_category = await category_service.update_category(
        category_id=category_id, category_in=category_in, user_id=current_user.id
    )
    if not updated_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return updated_category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    delete_on_spotify: bool = False,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_uow),
    user_spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
):
    """
    Deletes a category from the database and optionally from Spotify.
    """
    category_service = CategoryService(
        category_repo=uow.categories,
        style_repo=uow.styles,
        user_spotify_client=user_spotify_client,
    )
    deleted_category = await category_service.delete_category(
        category_id=category_id,
        delete_on_spotify=delete_on_spotify,
        user_id=current_user.id,
    )
    if not deleted_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )


@router.post("/categories/{category_id}/tracks", status_code=status.HTTP_200_OK)
async def add_track_to_category(
    category_id: int,
    track_in: CategoryTrackAdd,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    Adds a track to a category's Spotify playlist if it doesn't already exist.
    """
    success = await category_service.add_track_to_category_playlist(
        category_id=category_id,
        track_uri=track_in.track_uri,
        user_id=current_user.id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
