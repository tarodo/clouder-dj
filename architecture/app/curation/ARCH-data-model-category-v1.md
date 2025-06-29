---
id: ARCH-data-model-category
title: "Data Model: Category"
type: data_model
layer: domain
owner: '@team-backend'
version: v1
status: planned
created: 2025-06-28
updated: 2025-06-28
tags: [database, model, curation, category, spotify]
depends_on: []
referenced_by: []
---
## Context
This document describes the planned `Category` database model. This model will store user-defined categories for organizing music. Each category is linked to a specific user, a music style, and a corresponding Spotify playlist that is managed by the application.

## Structure
- **File:** `app/db/models/category.py` (new file)
- **Class:** `Category` (new SQLAlchemy model)

### Schema Definition
```python
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .style import Style

class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    style_id: Mapped[int] = mapped_column(ForeignKey("styles.id"), nullable=False)

    spotify_playlist_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    spotify_playlist_url: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped["User"] = relationship()
    style: Mapped["Style"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "style_id", "name", name="uq_category_user_style_name"),
    )
```

## Evolution
### Planned
- v1: Initial schema as defined above.

### Historical
- This is a new, planned component.
