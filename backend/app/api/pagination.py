from __future__ import annotations

import math
from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.per_page = per_page


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int

    @classmethod
    def create(
        cls, *, items: List[T], total: int, params: PaginationParams
    ) -> PaginatedResponse[T]:
        return cls(
            items=items,
            total=total,
            page=params.page,
            per_page=params.per_page,
            pages=math.ceil(total / params.per_page) if total > 0 else 1,
        )
