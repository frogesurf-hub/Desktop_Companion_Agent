from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryIdentityKey,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
)
from agent_core.memory.persistence.mapper import (
    memory_to_row,
    revision_to_row,
    row_to_memory,
    row_to_revision,
)
from agent_core.memory.persistence.orm import (
    MemoryRevisionRow,
    MemoryRow,
)


class SQLiteMemoryRepository:
    """
    MemoryRepository 的 SQLite / SQLAlchemy 实现。
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def create_memory(
        self,
        memory: Memory,
        initial_revision: MemoryRevision,
    ) -> None:
        """
        原子创建 Memory 与第一版 Revision。
        """

        if initial_revision.memory_id != memory.memory_id:
            raise ValueError(
                "Initial revision memory_id "
                "must match Memory memory_id"
            )

        if initial_revision.revision_number != 1:
            raise ValueError(
                "Initial revision_number must be 1"
            )

        if (
            initial_revision.lifecycle
            is not MemoryLifecycle.ACTIVE
        ):
            raise ValueError(
                "Initial revision must be ACTIVE"
            )

        async with self._session_factory() as session:
            async with session.begin():
                session.add(
                    memory_to_row(memory)
                )

                await session.flush()

                session.add(
                    revision_to_row(initial_revision)
                )

    async def get_memory(
        self,
        memory_id: UUID,
    ) -> Memory | None:
        async with self._session_factory() as session:
            row = await session.get(
                MemoryRow,
                str(memory_id),
            )

            if row is None:
                return None

            return row_to_memory(row)

    async def find_memory_by_identity(
        self,
        *,
        domain: MemoryDomain,
        scope: MemoryScope,
        identity_key: MemoryIdentityKey,
    ) -> Memory | None:
        """
        按 Domain、Scope 和 logical identity
        查找唯一的逻辑 Memory。
        """

        statement = select(MemoryRow).where(
            MemoryRow.domain == domain.value,
            MemoryRow.scope_kind == scope.kind.value,
            MemoryRow.identity_key == identity_key.value,
        )

        if (
            scope.kind
            is MemoryScopeKind.CHARACTER
        ):
            statement = statement.where(
                MemoryRow.character_id
                == scope.character_id
            )
        else:
            statement = statement.where(
                MemoryRow.character_id.is_(None)
            )

        async with self._session_factory() as session:
            result = await session.execute(
                statement
            )

            row = result.scalars().one_or_none()

            if row is None:
                return None

            return row_to_memory(row)

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[Memory, ...]:
        statement = select(MemoryRow)

        if domain is not None:
            statement = statement.where(
                MemoryRow.domain == domain.value
            )

        if scope is not None:
            statement = statement.where(
                MemoryRow.scope_kind
                == scope.kind.value
            )

            if (
                scope.kind
                is MemoryScopeKind.CHARACTER
            ):
                statement = statement.where(
                    MemoryRow.character_id
                    == scope.character_id
                )
            else:
                statement = statement.where(
                    MemoryRow.character_id.is_(None)
                )

        statement = statement.order_by(
            MemoryRow.memory_id
        )

        async with self._session_factory() as session:
            result = await session.execute(
                statement
            )

            rows = result.scalars().all()

            return tuple(
                row_to_memory(row)
                for row in rows
            )

    async def get_active_revision(
        self,
        memory_id: UUID,
    ) -> MemoryRevision | None:
        statement = (
            select(MemoryRevisionRow)
            .where(
                MemoryRevisionRow.memory_id
                == str(memory_id),
                MemoryRevisionRow.lifecycle
                == MemoryLifecycle.ACTIVE.value,
            )
        )

        async with self._session_factory() as session:
            result = await session.execute(
                statement
            )

            row = result.scalars().one_or_none()

            if row is None:
                return None

            return row_to_revision(row)

    async def list_revisions(
        self,
        memory_id: UUID,
    ) -> tuple[MemoryRevision, ...]:
        statement = (
            select(MemoryRevisionRow)
            .where(
                MemoryRevisionRow.memory_id
                == str(memory_id)
            )
            .order_by(
                MemoryRevisionRow.revision_number
            )
        )

        async with self._session_factory() as session:
            result = await session.execute(
                statement
            )

            rows = result.scalars().all()

            return tuple(
                row_to_revision(row)
                for row in rows
            )

    async def replace_active_revision(
        self,
        memory_id: UUID,
        new_revision: MemoryRevision,
    ) -> None:
        """
        原子 supersede 当前 ACTIVE Revision，
        并写入新的 ACTIVE Revision。
        """

        if new_revision.memory_id != memory_id:
            raise ValueError(
                "New revision memory_id "
                "must match target memory_id"
            )

        if (
            new_revision.lifecycle
            is not MemoryLifecycle.ACTIVE
        ):
            raise ValueError(
                "New revision must be ACTIVE"
            )

        async with self._session_factory() as session:
            async with session.begin():
                active_statement = (
                    select(MemoryRevisionRow)
                    .where(
                        MemoryRevisionRow.memory_id
                        == str(memory_id),
                        MemoryRevisionRow.lifecycle
                        == MemoryLifecycle.ACTIVE.value,
                    )
                )

                active_result = await session.execute(
                    active_statement
                )

                active_row = (
                    active_result.scalars().one_or_none()
                )

                if active_row is None:
                    raise ValueError(
                        "Memory has no ACTIVE revision"
                    )

                max_revision_statement = (
                    select(
                        func.max(
                            MemoryRevisionRow.revision_number
                        )
                    )
                    .where(
                        MemoryRevisionRow.memory_id
                        == str(memory_id)
                    )
                )

                max_revision_result = (
                    await session.execute(
                        max_revision_statement
                    )
                )

                max_revision_number = (
                    max_revision_result.scalar_one()
                )

                if max_revision_number is None:
                    raise ValueError(
                        "Memory has no revisions"
                    )

                expected_revision_number = (
                    max_revision_number + 1
                )

                if (
                    new_revision.revision_number
                    != expected_revision_number
                ):
                    raise ValueError(
                        "New revision_number must be "
                        f"{expected_revision_number}"
                    )

                active_row.lifecycle = (
                    MemoryLifecycle.SUPERSEDED.value
                )

                await session.flush()

                session.add(
                    revision_to_row(
                        new_revision
                    )
                )

    async def expire_active_revision(
        self,
        memory_id: UUID,
        expected_revision_number: int,
    ) -> None:
        """
        原子地将预期的当前 ACTIVE Revision 标记为 EXPIRED。
        """

        async with self._session_factory() as session:
            async with session.begin():
                expire_statement = (
                    update(MemoryRevisionRow)
                    .where(
                        MemoryRevisionRow.memory_id
                        == str(memory_id),
                        MemoryRevisionRow.revision_number
                        == expected_revision_number,
                        MemoryRevisionRow.lifecycle
                        == MemoryLifecycle.ACTIVE.value,
                    )
                    .values(
                        lifecycle=(
                            MemoryLifecycle.EXPIRED.value
                        )
                    )
                    .returning(
                        MemoryRevisionRow.row_id
                    )
                )

                result = await session.execute(
                    expire_statement
                )

                updated_row_id = (
                    result.scalar_one_or_none()
                )

                if updated_row_id is None:
                    raise ValueError(
                        "Expected ACTIVE revision "
                        "does not exist"
                    )
    async def delete_memory(
        self,
        memory_id: UUID,
        tombstone_revision: MemoryRevision,
    ) -> None:
        """
        原子清除已有 Revision 内容，
        并写入无内容 tombstone。
        """

        if tombstone_revision.memory_id != memory_id:
            raise ValueError(
                "Tombstone revision memory_id "
                "must match target memory_id"
            )

        if (
            tombstone_revision.lifecycle
            is not MemoryLifecycle.DELETED
        ):
            raise ValueError(
                "Tombstone revision must be DELETED"
            )

        async with self._session_factory() as session:
            async with session.begin():
                memory_row = await session.get(
                    MemoryRow,
                    str(memory_id),
                )

                if memory_row is None:
                    raise ValueError(
                        "Memory does not exist"
                    )

                max_revision_statement = (
                    select(
                        func.max(
                            MemoryRevisionRow.revision_number
                        )
                    )
                    .where(
                        MemoryRevisionRow.memory_id
                        == str(memory_id)
                    )
                )

                max_revision_result = (
                    await session.execute(
                        max_revision_statement
                    )
                )

                max_revision_number = (
                    max_revision_result.scalar_one()
                )

                if max_revision_number is None:
                    raise ValueError(
                        "Memory has no revisions"
                    )

                expected_revision_number = (
                    max_revision_number + 1
                )

                if (
                    tombstone_revision.revision_number
                    != expected_revision_number
                ):
                    raise ValueError(
                        "Tombstone revision_number "
                        "must be "
                        f"{expected_revision_number}"
                    )

                await session.execute(
                    delete(MemoryRevisionRow)
                    .where(
                        MemoryRevisionRow.memory_id
                        == str(memory_id)
                    )
                )

                session.add(
                    revision_to_row(
                        tombstone_revision
                    )
                )
