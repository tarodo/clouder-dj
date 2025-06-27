"""standardize enum casing

Revision ID: 1a2b3c4d5e6f
Revises: e5a4b3c2d1f0
Create Date: 2025-06-29 14:00:00.000000+00:00

"""

# mypy: ignore-errors

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, None] = "e5a4b3c2d1f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types
provider_enum_new = postgresql.ENUM(
    "BEATPORT", "SPOTIFY", "TIDAL", name="provider_enum"
)
entity_type_enum_new = postgresql.ENUM(
    "ARTIST", "LABEL", "RELEASE", "TRACK", name="entity_type_enum"
)

# Old enum types (for downgrade)
provider_enum_old = postgresql.ENUM(
    "BEATPORT", "SPOTIFY", "tidal", name="provider_enum"
)
entity_type_enum_old = postgresql.ENUM(
    "artist", "label", "release", "track", name="entity_type_enum"
)


def upgrade() -> None:
    # Standardize ExternalDataProvider enum
    op.execute("ALTER TYPE provider_enum RENAME TO provider_enum_old")
    provider_enum_new.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE external_data ALTER COLUMN provider TYPE provider_enum "
        "USING UPPER(provider::text)::provider_enum"
    )
    op.execute("DROP TYPE provider_enum_old")

    # Standardize ExternalDataEntityType enum
    op.execute("ALTER TYPE entity_type_enum RENAME TO entity_type_enum_old")
    entity_type_enum_new.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE external_data ALTER COLUMN entity_type TYPE entity_type_enum "
        "USING UPPER(entity_type::text)::entity_type_enum"
    )
    op.execute("DROP TYPE entity_type_enum_old")


def downgrade() -> None:
    # Revert ExternalDataProvider enum
    op.execute("ALTER TYPE provider_enum RENAME TO provider_enum_new")
    provider_enum_old.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE external_data ALTER COLUMN provider TYPE provider_enum "
        "USING (CASE provider::text WHEN 'TIDAL' THEN 'tidal' "
        "ELSE provider::text END)::provider_enum"
    )
    op.execute("DROP TYPE provider_enum_new")

    # Revert ExternalDataEntityType enum
    op.execute("ALTER TYPE entity_type_enum RENAME TO entity_type_enum_new")
    entity_type_enum_old.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE external_data ALTER COLUMN entity_type TYPE entity_type_enum "
        "USING LOWER(entity_type::text)::entity_type_enum"
    )
    op.execute("DROP TYPE entity_type_enum_new")
