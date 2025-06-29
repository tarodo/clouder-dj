from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_category_service, get_current_user
from app.db.models.user import User
from app.schemas.category import (
    Category,
    CategoryCreate,
    CategoryCreateResponse,
    CategoryUpdate,
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
    category_service: CategoryService = Depends(get_category_service),
) -> List[CategoryCreateResponse]:
    """
    Creates one or more new categories for the current user and a given style.
    This is a transactional operation that creates both a Spotify playlist
    and a database record for each category.
    """
    created_categories = await category_service.create_categories(
        categories_in=categories_in, user=current_user, style_id=style_id
    )
    return created_categories


@router.get("/styles/{style_id}/categories", response_model=List[Category])
async def get_categories(
    style_id: int,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service),
):
    """
    Lists all categories for the current user and a given style.
    """
    categories = await category_service.get_categories_by_style(
        user_id=current_user.id, style_id=style_id
    )
    return categories


@router.patch("/categories/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service),
) -> Category:
    """
    Updates the name of a category and its corresponding Spotify playlist.
    """
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
    category_service: CategoryService = Depends(get_category_service),
):
    """
    Deletes a category from the database and optionally from Spotify.
    """
    deleted = await category_service.delete_category(
        category_id=category_id,
        delete_on_spotify=delete_on_spotify,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
