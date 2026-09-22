import asyncio
import socket
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection
from websockets.asyncio.client import ClientConnection, connect

from agent_core.communication import WebSocketServer
from agent_core.core.message import Message
from agent_core.core.message_router import RuntimeMessageRouter
from agent_core.memory import (
    HealthAwareMemoryGovernanceService,
    Memory,
    MemoryCapability,
    MemoryDomain,
    MemoryGovernanceEntry,
    MemoryGovernanceService,
    MemoryHealthStatus,
    MemoryHealthTracker,
    MemoryLifecycle,
    MemoryRetrievalLimits,
    MemoryRetrievalPolicy,
    MemoryRetrievalService,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)
from agent_core.memory.persistence import (
    SQLiteMemoryRepository,
    create_memory_engine,
    create_memory_session_factory,
)
from agent_core.memory.persistence.orm import Base
from agent_core.memory.protocol import MemoryProtocolHandler
from agent_core.tests.fakes import FixedClock

_ACTIVE_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)

_EXPIRED_MEMORY_ID = UUID(
    "22345678-1234-5678-1234-567812345678"
)

_MISSING_MEMORY_ID = UUID(
    "32345678-1234-5678-1234-567812345678"
)

_INITIAL_RECORDED_AT = datetime(
    2026,
    9,
    22,
    12,
    0,
    tzinfo=UTC,
)

_MUTATION_RECORDED_AT = datetime(
    2026,
    9,
    22,
    13,
    0,
    tzinfo=UTC,
)


class RejectChatProcessor:
    async def process_message(
        self,
        message: Message,
    ) -> Message:
        raise AssertionError(
            "Chat processor should not be called"
        )


class FailingMemoryGovernance:
    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[
        MemoryGovernanceEntry,
        ...,
    ]:
        raise RuntimeError(
            "sensitive database failure"
        )

    async def inspect_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        raise RuntimeError(
            "sensitive database failure"
        )

    async def edit_memory(
        self,
        memory_id: UUID,
        new_content: str,
    ) -> MemoryGovernanceEntry:
        raise RuntimeError(
            "sensitive database failure"
        )

    async def delete_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        raise RuntimeError(
            "sensitive database failure"
        )

    async def get_history(
        self,
        memory_id: UUID,
    ) -> tuple[
        MemoryRevision,
        ...,
    ]:
        raise RuntimeError(
            "sensitive database failure"
        )


def _get_free_port() -> int:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:
        sock.bind(
            (
                "127.0.0.1",
                0,
            )
        )

        port = sock.getsockname()[1]

    assert isinstance(
        port,
        int,
    )

    return port


async def _connect_with_retry(
    uri: str,
) -> ClientConnection:
    last_error: OSError | None = None

    for _ in range(50):
        try:
            return await connect(
                uri,
                proxy=None,
            )

        except OSError as exc:
            last_error = exc

            await asyncio.sleep(
                0.01
            )

    raise AssertionError(
        "WebSocket server did not start in time"
    ) from last_error


async def _create_schema(
    connection: AsyncConnection,
) -> None:
    await connection.run_sync(
        Base.metadata.create_all,
    )


async def _send_request(
    client: ClientConnection,
    request: Message,
) -> Message:
    await client.send(
        request.to_json(),
    )

    raw_response = await client.recv()

    assert isinstance(
        raw_response,
        str,
    )

    return Message.from_json(
        raw_response
    )


async def _seed_memory(
    repository: SQLiteMemoryRepository,
    *,
    memory_id: UUID,
    domain: MemoryDomain,
    content: str,
) -> None:
    await repository.create_memory(
        Memory(
            memory_id=memory_id,
            domain=domain,
            scope=MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        ),
        MemoryRevision(
            memory_id=memory_id,
            revision_number=1,
            content=content,
            source=MemorySource.USER_EXPLICIT,
            lifecycle=MemoryLifecycle.ACTIVE,
            recorded_at=_INITIAL_RECORDED_AT,
        ),
    )


def test_memory_governance_round_trips_over_websocket_with_sqlite(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        engine = create_memory_engine(
            tmp_path / "memory.db"
        )

        try:
            async with engine.begin() as connection:
                await _create_schema(
                    connection
                )

            repository = SQLiteMemoryRepository(
                create_memory_session_factory(
                    engine
                )
            )

            await _seed_memory(
                repository,
                memory_id=_ACTIVE_MEMORY_ID,
                domain=MemoryDomain.USER_PROFILE,
                content="The user prefers Python.",
            )

            await _seed_memory(
                repository,
                memory_id=_EXPIRED_MEMORY_ID,
                domain=MemoryDomain.WORKING_CONTEXT,
                content="Temporary expired fact.",
            )

            await repository.expire_active_revision(
                _EXPIRED_MEMORY_ID,
                1,
            )

            health = MemoryHealthTracker()

            governance = (
                HealthAwareMemoryGovernanceService(
                    governance=MemoryGovernanceService(
                        repository=repository,
                        clock=FixedClock(
                            _MUTATION_RECORDED_AT
                        ),
                    ),
                    health=health,
                )
            )

            router = RuntimeMessageRouter(
                chat_processor=RejectChatProcessor(),
                memory_processor=MemoryProtocolHandler(
                    governance=governance,
                ),
            )

            port = _get_free_port()

            server = WebSocketServer(
                host="127.0.0.1",
                port=port,
                processor=router,
            )

            server_task = asyncio.create_task(
                server.run(),
            )

            try:
                client = await _connect_with_retry(
                    f"ws://127.0.0.1:{port}"
                )

                try:
                    initial_list = await _send_request(
                        client,
                        Message(
                            id="list-1",
                            type="memory.list",
                            source="desktop",
                            payload={},
                        ),
                    )

                    assert (
                        initial_list.type
                        == "memory.list.result"
                    )
                    assert (
                        initial_list.payload["request_id"]
                        == "list-1"
                    )

                    initial_ids = {
                        item["memory_id"]
                        for item in initial_list.payload[
                            "memories"
                        ]
                    }

                    assert str(
                        _ACTIVE_MEMORY_ID
                    ) in initial_ids
                    assert str(
                        _EXPIRED_MEMORY_ID
                    ) in initial_ids

                    inspect_response = await _send_request(
                        client,
                        Message(
                            id="inspect-1",
                            type="memory.inspect",
                            source="desktop",
                            payload={
                                "memory_id": str(
                                    _ACTIVE_MEMORY_ID
                                ),
                            },
                        ),
                    )

                    assert (
                        inspect_response.type
                        == "memory.inspect.result"
                    )
                    assert (
                        inspect_response.payload[
                            "request_id"
                        ]
                        == "inspect-1"
                    )
                    assert (
                        inspect_response.payload[
                            "memory"
                        ][
                            "latest_revision"
                        ][
                            "content"
                        ]
                        == "The user prefers Python."
                    )

                    edit_response = await _send_request(
                        client,
                        Message(
                            id="edit-1",
                            type="memory.edit",
                            source="desktop",
                            payload={
                                "memory_id": str(
                                    _ACTIVE_MEMORY_ID
                                ),
                                "content": (
                                    "The user prefers C#."
                                ),
                            },
                        ),
                    )

                    assert (
                        edit_response.type
                        == "memory.edit.result"
                    )

                    edited_revision = (
                        edit_response.payload[
                            "memory"
                        ][
                            "latest_revision"
                        ]
                    )

                    assert (
                        edited_revision[
                            "revision_number"
                        ]
                        == 2
                    )
                    assert (
                        edited_revision["content"]
                        == "The user prefers C#."
                    )
                    assert (
                        edited_revision["source"]
                        == "user_edit"
                    )

                    history_response = await _send_request(
                        client,
                        Message(
                            id="history-1",
                            type="memory.history",
                            source="desktop",
                            payload={
                                "memory_id": str(
                                    _ACTIVE_MEMORY_ID
                                ),
                            },
                        ),
                    )

                    revisions = history_response.payload[
                        "revisions"
                    ]

                    assert len(
                        revisions
                    ) == 2
                    assert (
                        revisions[0]["lifecycle"]
                        == "superseded"
                    )
                    assert (
                        revisions[1]["lifecycle"]
                        == "active"
                    )

                    invalid_response = await _send_request(
                        client,
                        Message(
                            id="invalid-1",
                            type="memory.inspect",
                            source="desktop",
                            payload={
                                "memory_id": "not-a-uuid",
                            },
                        ),
                    )

                    assert invalid_response.payload == {
                        "request_id": "invalid-1",
                        "code": "MEMORY_INVALID_REQUEST",
                        "message": (
                            "Invalid Memory request."
                        ),
                    }

                    surviving_response = (
                        await _send_request(
                            client,
                            Message(
                                id="list-2",
                                type="memory.list",
                                source="desktop",
                                payload={},
                            ),
                        )
                    )

                    assert (
                        surviving_response.type
                        == "memory.list.result"
                    )

                    missing_response = await _send_request(
                        client,
                        Message(
                            id="missing-1",
                            type="memory.inspect",
                            source="desktop",
                            payload={
                                "memory_id": str(
                                    _MISSING_MEMORY_ID
                                ),
                            },
                        ),
                    )

                    assert (
                        missing_response.payload["code"]
                        == "MEMORY_NOT_FOUND"
                    )

                    invalid_state_response = (
                        await _send_request(
                            client,
                            Message(
                                id="expired-edit-1",
                                type="memory.edit",
                                source="desktop",
                                payload={
                                    "memory_id": str(
                                        _EXPIRED_MEMORY_ID
                                    ),
                                    "content": (
                                        "Replacement content."
                                    ),
                                },
                            ),
                        )
                    )

                    assert (
                        invalid_state_response.payload[
                            "code"
                        ]
                        == "MEMORY_INVALID_STATE"
                    )

                    delete_response = await _send_request(
                        client,
                        Message(
                            id="delete-1",
                            type="memory.delete",
                            source="desktop",
                            payload={
                                "memory_id": str(
                                    _ACTIVE_MEMORY_ID
                                ),
                            },
                        ),
                    )

                    deleted_revision = (
                        delete_response.payload[
                            "memory"
                        ][
                            "latest_revision"
                        ]
                    )

                    assert (
                        deleted_revision["lifecycle"]
                        == "deleted"
                    )
                    assert (
                        deleted_revision["content"]
                        is None
                    )
                    assert (
                        deleted_revision[
                            "revision_number"
                        ]
                        == 3
                    )

                    inspect_deleted = await _send_request(
                        client,
                        Message(
                            id="inspect-deleted-1",
                            type="memory.inspect",
                            source="desktop",
                            payload={
                                "memory_id": str(
                                    _ACTIVE_MEMORY_ID
                                ),
                            },
                        ),
                    )

                    assert (
                        inspect_deleted.payload[
                            "memory"
                        ][
                            "latest_revision"
                        ][
                            "lifecycle"
                        ]
                        == "deleted"
                    )
                    assert (
                        inspect_deleted.payload[
                            "memory"
                        ][
                            "latest_revision"
                        ][
                            "content"
                        ]
                        is None
                    )

                    deleted_history = await _send_request(
                        client,
                        Message(
                            id="history-deleted-1",
                            type="memory.history",
                            source="desktop",
                            payload={
                                "memory_id": str(
                                    _ACTIVE_MEMORY_ID
                                ),
                            },
                        ),
                    )

                    deleted_revisions = (
                        deleted_history.payload[
                            "revisions"
                        ]
                    )

                    assert len(
                        deleted_revisions
                    ) == 1
                    assert (
                        deleted_revisions[0][
                            "lifecycle"
                        ]
                        == "deleted"
                    )
                    assert (
                        deleted_revisions[0]["content"]
                        is None
                    )
                    assert (
                        "The user prefers"
                        not in deleted_history.to_json()
                    )

                    edit_deleted = await _send_request(
                        client,
                        Message(
                            id="edit-deleted-1",
                            type="memory.edit",
                            source="desktop",
                            payload={
                                "memory_id": str(
                                    _ACTIVE_MEMORY_ID
                                ),
                                "content": (
                                    "Must not be restored."
                                ),
                            },
                        ),
                    )

                    assert (
                        edit_deleted.payload["code"]
                        == "MEMORY_DELETED"
                    )

                    final_list = await _send_request(
                        client,
                        Message(
                            id="list-3",
                            type="memory.list",
                            source="desktop",
                            payload={},
                        ),
                    )

                    final_ids = {
                        item["memory_id"]
                        for item in final_list.payload[
                            "memories"
                        ]
                    }

                    assert str(
                        _ACTIVE_MEMORY_ID
                    ) not in final_ids

                    retrieval = MemoryRetrievalService(
                        repository=repository,
                        policy=MemoryRetrievalPolicy(
                            limits=(
                                MemoryRetrievalLimits()
                            ),
                        ),
                    )

                    prepared_context = (
                        await retrieval.retrieve(
                            "C#",
                            character_id="aria",
                        )
                    )

                    assert (
                        "The user prefers C#."
                        not in prepared_context.user_profile
                    )

                    governance_health = (
                        health.snapshot().for_capability(
                            MemoryCapability.GOVERNANCE
                        )
                    )

                    assert (
                        governance_health.status
                        is MemoryHealthStatus.AVAILABLE
                    )

                finally:
                    await client.close()

            finally:
                server_task.cancel()

                with suppress(
                    asyncio.CancelledError
                ):
                    await server_task

        finally:
            await engine.dispose()

    asyncio.run(
        scenario()
    )


def test_websocket_memory_infrastructure_failure_is_safe_and_degrades_health(
) -> None:
    async def scenario() -> None:
        health = MemoryHealthTracker()

        governance = (
            HealthAwareMemoryGovernanceService(
                governance=FailingMemoryGovernance(),
                health=health,
            )
        )

        router = RuntimeMessageRouter(
            chat_processor=RejectChatProcessor(),
            memory_processor=MemoryProtocolHandler(
                governance=governance,
            ),
        )

        port = _get_free_port()

        server = WebSocketServer(
            host="127.0.0.1",
            port=port,
            processor=router,
        )

        server_task = asyncio.create_task(
            server.run(),
        )

        try:
            client = await _connect_with_retry(
                f"ws://127.0.0.1:{port}"
            )

            try:
                response = await _send_request(
                    client,
                    Message(
                        id="failure-1",
                        type="memory.list",
                        source="desktop",
                        payload={},
                    ),
                )

                assert response.type == "error"
                assert response.payload == {
                    "request_id": "failure-1",
                    "code": (
                        "MEMORY_OPERATION_FAILED"
                    ),
                    "message": (
                        "Memory operation failed."
                    ),
                }

                assert (
                    "sensitive database failure"
                    not in response.to_json()
                )

                governance_health = (
                    health.snapshot().for_capability(
                        MemoryCapability.GOVERNANCE
                    )
                )

                assert (
                    governance_health.status
                    is MemoryHealthStatus.DEGRADED
                )
                assert (
                    governance_health.last_error_type
                    == "RuntimeError"
                )

            finally:
                await client.close()

        finally:
            server_task.cancel()

            with suppress(
                asyncio.CancelledError
            ):
                await server_task

    asyncio.run(
        scenario()
    )
