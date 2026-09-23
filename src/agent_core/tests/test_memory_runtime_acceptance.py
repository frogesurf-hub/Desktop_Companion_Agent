import asyncio
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from agent_core.core.message import Message
from agent_core.memory import (
    Memory,
    MemoryDomain,
    MemoryIdentityKey,
    MemoryLifecycle,
    MemoryRetrievalLimits,
    MemoryRetrievalPolicy,
    MemoryRetrievalService,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)
from agent_core.memory.governance import (
    MemoryGovernanceService,
)
from agent_core.memory.persistence import (
    SQLiteMemoryRepository,
    create_memory_engine,
    create_memory_session_factory,
    upgrade_memory_database,
)
from agent_core.providers import (
    LLMResponse,
)
from agent_core.tests.fakes import (
    FakeLLMProvider,
    FixedClock,
    create_test_agent,
)

_MEMORY_ID = UUID(
    "11111111-2222-3333-4444-555555555555"
)

_RECORDED_AT = datetime(
    2026,
    9,
    23,
    12,
    0,
    tzinfo=UTC,
)

_EDITED_AT = datetime(
    2026,
    9,
    23,
    13,
    0,
    tzinfo=UTC,
)

_DELETED_AT = datetime(
    2026,
    9,
    23,
    14,
    0,
    tzinfo=UTC,
)

_ORIGINAL_CONTENT = (
    "The user prefers C# for game development."
)

_CORRECTED_CONTENT = (
    "The user prefers Rust for game development."
)


def test_memory_runtime_lifecycle_survives_restart_and_reaches_provider(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "memory.db"
    )

    upgrade_memory_database(
        database_path
    )

    asyncio.run(
        _exercise_runtime_lifecycle(
            database_path
        )
    )


async def _exercise_runtime_lifecycle(
    database_path: Path,
) -> None:
    first_engine = create_memory_engine(
        database_path
    )

    try:
        first_repository = (
            SQLiteMemoryRepository(
                create_memory_session_factory(
                    first_engine
                )
            )
        )

        memory = Memory(
            memory_id=_MEMORY_ID,
            domain=MemoryDomain.USER_PROFILE,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
            identity_key=MemoryIdentityKey(
                "user_profile.preference."
                "game_development.programming_language"
            ),
        )

        revision = MemoryRevision(
            memory_id=_MEMORY_ID,
            revision_number=1,
            content=_ORIGINAL_CONTENT,
            source=(
                MemorySource
                .AUTOMATIC_EXPLICIT_FACT
            ),
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=_RECORDED_AT,
        )

        await first_repository.create_memory(
            memory,
            revision,
        )

    finally:
        await first_engine.dispose()

    second_engine = create_memory_engine(
        database_path
    )

    try:
        repository = SQLiteMemoryRepository(
            create_memory_session_factory(
                second_engine
            )
        )

        persisted_memory = (
            await repository.get_memory(
                _MEMORY_ID
            )
        )

        persisted_revision = (
            await repository.get_active_revision(
                _MEMORY_ID
            )
        )

        assert persisted_memory == memory
        assert persisted_revision == revision

        retriever = MemoryRetrievalService(
            repository=repository,
            policy=MemoryRetrievalPolicy(
                limits=MemoryRetrievalLimits(),
            ),
        )

        initial_provider = FakeLLMProvider(
            response=LLMResponse(
                content="Initial response.",
            )
        )

        initial_agent = create_test_agent(
            initial_provider,
            memory_retriever=retriever,
        )

        initial_response = (
            await initial_agent.process_message(
                Message(
                    type="chat",
                    source="desktop",
                    payload={
                        "message": (
                            "What programming language "
                            "do I prefer for game development?"
                        ),
                    },
                )
            )
        )

        assert initial_response.type == "response"

        initial_system_content = (
            initial_provider.requests[0]
            .messages[0]
            .content
        )

        assert (
            "[Memory Context]"
            in initial_system_content
        )

        assert (
            _ORIGINAL_CONTENT
            in initial_system_content
        )

        governance = MemoryGovernanceService(
            repository=repository,
            clock=FixedClock(
                _EDITED_AT
            ),
        )

        edited_entry = (
            await governance.edit_memory(
                _MEMORY_ID,
                _CORRECTED_CONTENT,
            )
        )

        assert (
            edited_entry.latest_revision
            .revision_number
            == 2
        )

        assert (
            edited_entry.latest_revision.source
            is MemorySource.USER_EDIT
        )

        assert (
            edited_entry.latest_revision.lifecycle
            is MemoryLifecycle.ACTIVE
        )

        history = (
            await governance.get_history(
                _MEMORY_ID
            )
        )

        assert len(history) == 2

        assert (
            history[0].lifecycle
            is MemoryLifecycle.SUPERSEDED
        )

        assert (
            history[1].lifecycle
            is MemoryLifecycle.ACTIVE
        )

        corrected_context = (
            await retriever.retrieve(
                "game development language",
                character_id="test",
            )
        )

        assert (
            _CORRECTED_CONTENT
            in corrected_context.user_profile
        )

        assert (
            _ORIGINAL_CONTENT
            not in corrected_context.user_profile
        )

        corrected_provider = FakeLLMProvider(
            response=LLMResponse(
                content="Corrected response.",
            )
        )

        corrected_agent = create_test_agent(
            corrected_provider,
            memory_retriever=retriever,
        )

        await corrected_agent.process_message(
            Message(
                type="chat",
                source="desktop",
                payload={
                    "message": (
                        "Remind me which language "
                        "I prefer."
                    ),
                },
            )
        )

        corrected_system_content = (
            corrected_provider.requests[0]
            .messages[0]
            .content
        )

        assert (
            _CORRECTED_CONTENT
            in corrected_system_content
        )

        assert (
            _ORIGINAL_CONTENT
            not in corrected_system_content
        )

        delete_governance = (
            MemoryGovernanceService(
                repository=repository,
                clock=FixedClock(
                    _DELETED_AT
                ),
            )
        )

        deleted_entry = (
            await delete_governance.delete_memory(
                _MEMORY_ID
            )
        )

        assert (
            deleted_entry.latest_revision
            .revision_number
            == 3
        )

        assert (
            deleted_entry.latest_revision.lifecycle
            is MemoryLifecycle.DELETED
        )

        assert (
            deleted_entry.latest_revision.content
            is None
        )

        deleted_history = (
            await delete_governance.get_history(
                _MEMORY_ID
            )
        )

        assert len(deleted_history) == 1

        assert (
            deleted_history[0].lifecycle
            is MemoryLifecycle.DELETED
        )

        assert deleted_history[0].content is None

        deleted_context = (
            await retriever.retrieve(
                "game development language",
                character_id="test",
            )
        )

        assert deleted_context.user_profile == ()

        deleted_provider = FakeLLMProvider(
            response=LLMResponse(
                content="Post-delete response.",
            )
        )

        deleted_agent = create_test_agent(
            deleted_provider,
            memory_retriever=retriever,
        )

        await deleted_agent.process_message(
            Message(
                type="chat",
                source="desktop",
                payload={
                    "message": (
                        "What programming language "
                        "do I prefer?"
                    ),
                },
            )
        )

        deleted_system_content = (
            deleted_provider.requests[0]
            .messages[0]
            .content
        )

        assert (
            _ORIGINAL_CONTENT
            not in deleted_system_content
        )

        assert (
            _CORRECTED_CONTENT
            not in deleted_system_content
        )

        assert (
            "[Memory Context]"
            not in deleted_system_content
        )

    finally:
        await second_engine.dispose()
