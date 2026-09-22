import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest

from agent_core.core.message import Message
from agent_core.memory.governance import (
    MemoryDeletedError,
    MemoryGovernanceEntry,
    MemoryNotFoundError,
    MemoryStateError,
)
from agent_core.memory.models import (
    Memory,
    MemoryDomain,
    MemoryIdentityKey,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
)
from agent_core.memory.protocol import (
    MemoryProtocolHandler,
)

_MEMORY_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)

_RECORDED_AT = datetime(
    2026,
    9,
    20,
    12,
    0,
    tzinfo=UTC,
)


def _active_entry() -> MemoryGovernanceEntry:
    memory = Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.USER_PROFILE,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
        identity_key=MemoryIdentityKey(
            "user_profile.preference.programming_language"
        ),
    )

    revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=2,
        content="The user prefers C#.",
        source=MemorySource.USER_EDIT,
        lifecycle=MemoryLifecycle.ACTIVE,
        recorded_at=_RECORDED_AT,
    )

    return MemoryGovernanceEntry(
        memory=memory,
        latest_revision=revision,
    )


def _deleted_entry() -> MemoryGovernanceEntry:
    memory = Memory(
        memory_id=_MEMORY_ID,
        domain=MemoryDomain.USER_PROFILE,
        scope=MemoryScope(
            kind=MemoryScopeKind.GLOBAL_USER,
        ),
    )

    revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=3,
        content=None,
        source=MemorySource.USER_EDIT,
        lifecycle=MemoryLifecycle.DELETED,
        recorded_at=_RECORDED_AT,
    )

    return MemoryGovernanceEntry(
        memory=memory,
        latest_revision=revision,
    )


class FakeMemoryGovernance:
    def __init__(
        self,
        *,
        entries: tuple[
            MemoryGovernanceEntry,
            ...,
        ] = (),
        entry: MemoryGovernanceEntry | None = None,
        revisions: tuple[
            MemoryRevision,
            ...,
        ] = (),
        error: Exception | None = None,
    ) -> None:
        self.entries = entries
        self.entry = (
            entry
            if entry is not None
            else _active_entry()
        )
        self.revisions = revisions
        self.error = error

        self.list_calls: list[
            tuple[
                MemoryDomain | None,
                MemoryScope | None,
            ]
        ] = []

        self.inspect_calls: list[UUID] = []
        self.edit_calls: list[
            tuple[
                UUID,
                str,
            ]
        ] = []
        self.delete_calls: list[UUID] = []
        self.history_calls: list[UUID] = []

    def _raise_if_needed(self) -> None:
        if self.error is not None:
            raise self.error

    async def list_memories(
        self,
        *,
        domain: MemoryDomain | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[
        MemoryGovernanceEntry,
        ...,
    ]:
        self._raise_if_needed()

        self.list_calls.append(
            (
                domain,
                scope,
            )
        )

        return self.entries

    async def inspect_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        self._raise_if_needed()

        self.inspect_calls.append(
            memory_id
        )

        return self.entry

    async def edit_memory(
        self,
        memory_id: UUID,
        new_content: str,
    ) -> MemoryGovernanceEntry:
        self._raise_if_needed()

        self.edit_calls.append(
            (
                memory_id,
                new_content,
            )
        )

        return self.entry

    async def delete_memory(
        self,
        memory_id: UUID,
    ) -> MemoryGovernanceEntry:
        self._raise_if_needed()

        self.delete_calls.append(
            memory_id
        )

        return self.entry

    async def get_history(
        self,
        memory_id: UUID,
    ) -> tuple[
        MemoryRevision,
        ...,
    ]:
        self._raise_if_needed()

        self.history_calls.append(
            memory_id
        )

        return self.revisions


def _request(
    message_type: str,
    payload: dict[str, Any],
) -> Message:
    return Message(
        id="request-1",
        type=message_type,
        source="desktop",
        payload=payload,
    )


def test_memory_list_serializes_visible_entries_and_filters(
) -> None:
    active = _active_entry()
    deleted = _deleted_entry()

    governance = FakeMemoryGovernance(
        entries=(
            active,
            deleted,
        )
    )

    handler = MemoryProtocolHandler(
        governance=governance
    )

    response = asyncio.run(
        handler.process_message(
            _request(
                "memory.list",
                {
                    "domain": "user_profile",
                    "scope": {
                        "kind": "global_user",
                    },
                },
            )
        )
    )

    assert response.type == "memory.list.result"
    assert (
        response.payload["request_id"]
        == "request-1"
    )

    assert governance.list_calls == [
        (
            MemoryDomain.USER_PROFILE,
            MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            ),
        )
    ]

    memories = response.payload[
        "memories"
    ]

    assert isinstance(
        memories,
        list,
    )

    assert len(memories) == 1

    serialized = memories[0]

    assert (
        serialized["memory_id"]
        == str(_MEMORY_ID)
    )
    assert (
        serialized["domain"]
        == "user_profile"
    )
    assert serialized["scope"] == {
        "kind": "global_user",
        "character_id": None,
    }
    assert (
        serialized["identity_key"]
        == (
            "user_profile.preference."
            "programming_language"
        )
    )

    latest = serialized[
        "latest_revision"
    ]

    assert latest["revision_number"] == 2
    assert (
        latest["content"]
        == "The user prefers C#."
    )
    assert latest["source"] == "user_edit"
    assert latest["lifecycle"] == "active"


def test_memory_inspect_serializes_entry() -> None:
    governance = FakeMemoryGovernance(
        entry=_active_entry()
    )

    handler = MemoryProtocolHandler(
        governance=governance
    )

    response = asyncio.run(
        handler.process_message(
            _request(
                "memory.inspect",
                {
                    "memory_id": str(
                        _MEMORY_ID
                    ),
                },
            )
        )
    )

    assert response.type == "memory.inspect.result"

    assert (
        response.payload["request_id"]
        == "request-1"
    )

    assert governance.inspect_calls == [
        _MEMORY_ID,
    ]

    memory = response.payload[
        "memory"
    ]

    assert (
        memory["latest_revision"][
            "recorded_at"
        ]
        == _RECORDED_AT.isoformat()
    )


def test_memory_edit_calls_governance() -> None:
    governance = FakeMemoryGovernance(
        entry=_active_entry()
    )

    handler = MemoryProtocolHandler(
        governance=governance
    )

    response = asyncio.run(
        handler.process_message(
            _request(
                "memory.edit",
                {
                    "memory_id": str(
                        _MEMORY_ID
                    ),
                    "content": (
                        "The user prefers C#."
                    ),
                },
            )
        )
    )

    assert response.type == "memory.edit.result"

    assert governance.edit_calls == [
        (
            _MEMORY_ID,
            "The user prefers C#.",
        )
    ]


def test_memory_delete_returns_tombstone() -> None:
    governance = FakeMemoryGovernance(
        entry=_deleted_entry()
    )

    handler = MemoryProtocolHandler(
        governance=governance
    )

    response = asyncio.run(
        handler.process_message(
            _request(
                "memory.delete",
                {
                    "memory_id": str(
                        _MEMORY_ID
                    ),
                },
            )
        )
    )

    assert response.type == "memory.delete.result"

    assert governance.delete_calls == [
        _MEMORY_ID,
    ]

    latest = response.payload[
        "memory"
    ][
        "latest_revision"
    ]

    assert latest["lifecycle"] == "deleted"
    assert latest["content"] is None


def test_memory_history_serializes_revisions() -> None:
    first_revision = MemoryRevision(
        memory_id=_MEMORY_ID,
        revision_number=1,
        content="The user prefers Python.",
        source=MemorySource.USER_EXPLICIT,
        lifecycle=MemoryLifecycle.SUPERSEDED,
        recorded_at=_RECORDED_AT,
    )

    second_revision = (
        _active_entry().latest_revision
    )

    governance = FakeMemoryGovernance(
        revisions=(
            first_revision,
            second_revision,
        )
    )

    handler = MemoryProtocolHandler(
        governance=governance
    )

    response = asyncio.run(
        handler.process_message(
            _request(
                "memory.history",
                {
                    "memory_id": str(
                        _MEMORY_ID
                    ),
                },
            )
        )
    )

    assert response.type == "memory.history.result"

    assert (
        response.payload["request_id"]
        == "request-1"
    )

    assert (
        response.payload["memory_id"]
        == str(_MEMORY_ID)
    )

    revisions = response.payload[
        "revisions"
    ]

    assert len(revisions) == 2
    assert (
        revisions[0]["lifecycle"]
        == "superseded"
    )
    assert (
        revisions[1]["lifecycle"]
        == "active"
    )


@pytest.mark.parametrize(
    (
        "message_type",
        "payload",
    ),
    [
        (
            "memory.unknown",
            {},
        ),
        (
            "memory.inspect",
            {},
        ),
        (
            "memory.inspect",
            {
                "memory_id": "not-a-uuid",
            },
        ),
        (
            "memory.list",
            {
                "domain": "unknown",
            },
        ),
        (
            "memory.list",
            {
                "scope": {
                    "kind": "character",
                    "character_id": "",
                },
            },
        ),
        (
            "memory.edit",
            {
                "memory_id": str(
                    _MEMORY_ID
                ),
                "content": "   ",
            },
        ),
        (
            "memory.list",
            {
                "domain": "user_profile",
                "scope": {
                    "kind": "character",
                    "character_id": "aria",
                },
            },
        ),
        (
            "memory.list",
            {
                "domain": "relationship",
                "scope": {
                    "kind": "global_user",
                },
            },
        ),
    ],
)
def test_invalid_memory_requests_are_rejected(
    message_type: str,
    payload: dict[str, Any],
) -> None:
    governance = FakeMemoryGovernance()

    handler = MemoryProtocolHandler(
        governance=governance
    )
    response = asyncio.run(
        handler.process_message(
            _request(
                message_type,
                payload,
            )
        )
    )

    assert response.type == "error"

    assert response.payload == {
        "request_id": "request-1",
        "code": "MEMORY_INVALID_REQUEST",
        "message": "Invalid Memory request.",
    }
    assert governance.list_calls == []
    assert governance.inspect_calls == []
    assert governance.edit_calls == []
    assert governance.delete_calls == []
    assert governance.history_calls == []


@pytest.mark.parametrize(
    (
        "error",
        "expected_code",
        "expected_message",
    ),
    [
        (
            MemoryNotFoundError(
                "sensitive missing detail"
            ),
            "MEMORY_NOT_FOUND",
            "Memory does not exist.",
        ),
        (
            MemoryDeletedError(
                "sensitive deleted detail"
            ),
            "MEMORY_DELETED",
            "Memory is deleted.",
        ),
        (
            MemoryStateError(
                "sensitive state detail"
            ),
            "MEMORY_INVALID_STATE",
            (
                "Memory is in an invalid state "
                "for this operation."
            ),
        ),
        (
            RuntimeError(
                "sensitive database detail"
            ),
            "MEMORY_OPERATION_FAILED",
            "Memory operation failed.",
        ),
    ],
)
def test_memory_errors_map_to_safe_protocol_errors(
    error: Exception,
    expected_code: str,
    expected_message: str,
) -> None:
    handler = MemoryProtocolHandler(
        governance=FakeMemoryGovernance(
            error=error
        )
    )

    response = asyncio.run(
        handler.process_message(
            _request(
                "memory.inspect",
                {
                    "memory_id": str(
                        _MEMORY_ID
                    ),
                },
            )
        )
    )

    assert response.type == "error"

    assert (
        response.payload["request_id"]
        == "request-1"
    )
    assert (
        response.payload["code"]
        == expected_code
    )
    assert (
        response.payload["message"]
        == expected_message
    )

    serialized_response = (
        response.to_json()
    )

    assert "sensitive" not in serialized_response
