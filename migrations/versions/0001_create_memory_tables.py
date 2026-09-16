"""Create Phase 4 Memory tables.

Revision ID: 0001_memory
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_memory"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column(
            "memory_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "domain",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "scope_kind",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "character_id",
            sa.String(length=128),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "memory_id",
        ),
    )

    op.create_table(
        "memory_revisions",
        sa.Column(
            "row_id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "memory_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "revision_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "lifecycle",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "recorded_at",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.String(length=40),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["memory_id"],
            ["memories.memory_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "row_id",
        ),
        sa.UniqueConstraint(
            "memory_id",
            "revision_number",
            name="uq_memory_revision_number",
        ),
    )

    op.create_index(
        op.f(
            "ix_memory_revisions_memory_id"
        ),
        "memory_revisions",
        ["memory_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_memory_revisions_lifecycle"
        ),
        "memory_revisions",
        ["lifecycle"],
        unique=False,
    )

    op.create_index(
        "uq_memory_active_revision",
        "memory_revisions",
        ["memory_id"],
        unique=True,
        sqlite_where=sa.text(
            "lifecycle = 'active'"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_memory_active_revision",
        table_name="memory_revisions",
    )

    op.drop_index(
        op.f(
            "ix_memory_revisions_lifecycle"
        ),
        table_name="memory_revisions",
    )

    op.drop_index(
        op.f(
            "ix_memory_revisions_memory_id"
        ),
        table_name="memory_revisions",
    )

    op.drop_table(
        "memory_revisions"
    )

    op.drop_table(
        "memories"
    )
