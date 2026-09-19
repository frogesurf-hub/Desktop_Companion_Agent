"""Add logical Memory identity key.

Revision ID: 0002_identity_key
Revises: 0001_memory
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_identity_key"
down_revision: str | None = "0001_memory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "memories",
        sa.Column(
            "identity_key",
            sa.String(length=256),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "memories",
        "identity_key",
    )
