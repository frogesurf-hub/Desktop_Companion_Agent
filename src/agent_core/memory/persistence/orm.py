from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    """
    Phase 4 Memory persistence 的 SQLAlchemy Base。
    """

    pass


class MemoryRow(Base):
    """
    逻辑 Memory 的数据库表示。

    这是 Persistence Model，不是 Domain Model。
    """

    __tablename__ = "memories"

    memory_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    domain: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    scope_kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    character_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    identity_key: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )


class MemoryRevisionRow(Base):
    """
    Memory Revision 的数据库表示。
    """

    __tablename__ = "memory_revisions"

    __table_args__ = (
        UniqueConstraint(
            "memory_id",
            "revision_number",
            name="uq_memory_revision_number",
        ),
        Index(
            "uq_memory_active_revision",
            "memory_id",
            unique=True,
            sqlite_where=text(
                "lifecycle = 'active'"
            ),
        ),
    )

    row_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    memory_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "memories.memory_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    revision_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    lifecycle: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    recorded_at: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    occurred_at: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
