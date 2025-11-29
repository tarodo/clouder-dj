"""add deleted status

Revision ID: 8f2327e28936
Revises: 4b5c6d7e8f9a
Create Date: 2025-11-29 12:00:00.000000+00:00

"""

# mypy: ignore-errors

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8f2327e28936"
down_revision: Union[str, None] = "4b5c6d7e8f9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE raw_layer_block_status_enum ADD VALUE 'DELETED'")


def downgrade() -> None:
    pass
