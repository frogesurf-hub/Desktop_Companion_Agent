"""Add logical Memory identity uniqueness.

Revision ID: 0003_identity_unique
Revises: 0002_identity_key
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_identity_unique"
down_revision: str | None = "0002_identity_key"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_memory_global_identity",
        "memories",
        [
            "domain",
            "scope_kind",
            "identity_key",
        ],
        unique=True,
        sqlite_where=sa.text(
            "identity_key IS NOT NULL "
            "AND scope_kind = 'global_user' "
            "AND character_id IS NULL"
        ),
    )

    op.create_index(
        "uq_memory_character_identity",
        "memories",
        [
            "domain",
            "scope_kind",
            "character_id",
            "identity_key",
        ],
        unique=True,
        sqlite_where=sa.text(
            "identity_key IS NOT NULL "
            "AND scope_kind = 'character' "
            "AND character_id IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_memory_character_identity",
        table_name="memories",
    )

    op.drop_index(
        "uq_memory_global_identity",
        table_name="memories",
    )
