import logging
from typing import Any
from uuid import UUID

from agent_core.core.message import Message
from agent_core.memory.governance import (
    MemoryDeletedError,
    MemoryGovernance,
    MemoryGovernanceEntry,
    MemoryGovernanceError,
    MemoryNotFoundError,
    MemoryStateError,
)
from agent_core.memory.models import (
    MemoryDomain,
    MemoryLifecycle,
    MemoryRevision,
    MemoryScope,
    MemoryScopeKind,
)

logger = logging.getLogger(__name__)


class _MemoryProtocolRequestError(Exception):
    """
    Memory protocol request validation failure.
    """


class MemoryProtocolHandler:
    """
    Desktop-facing Memory Governance protocol boundary.

    负责：
    - memory.* request dispatch
    - payload validation
    - protocol/domain conversion
    - safe result serialization
    - safe error mapping
    """

    def __init__(
        self,
        *,
        governance: MemoryGovernance,
    ) -> None:
        self._governance = governance

    async def process_message(
        self,
        message: Message,
    ) -> Message:
        try:
            if message.type == "memory.list":
                return await self._list_memories(
                    message
                )

            if message.type == "memory.inspect":
                return await self._inspect_memory(
                    message
                )

            if message.type == "memory.edit":
                return await self._edit_memory(
                    message
                )

            if message.type == "memory.delete":
                return await self._delete_memory(
                    message
                )

            if message.type == "memory.history":
                return await self._get_history(
                    message
                )

            raise _MemoryProtocolRequestError(
                "Unsupported Memory request"
            )

        except _MemoryProtocolRequestError:
            return self._error_response(
                request=message,
                code="MEMORY_INVALID_REQUEST",
                safe_message="Invalid Memory request.",
            )

        except MemoryNotFoundError:
            return self._error_response(
                request=message,
                code="MEMORY_NOT_FOUND",
                safe_message="Memory does not exist.",
            )

        except MemoryDeletedError:
            return self._error_response(
                request=message,
                code="MEMORY_DELETED",
                safe_message="Memory is deleted.",
            )

        except MemoryStateError:
            return self._error_response(
                request=message,
                code="MEMORY_INVALID_STATE",
                safe_message=(
                    "Memory is in an invalid state "
                    "for this operation."
                ),
            )

        except MemoryGovernanceError:
            return self._error_response(
                request=message,
                code="MEMORY_OPERATION_FAILED",
                safe_message="Memory operation failed.",
            )

        except Exception as exc:
            logger.warning(
                "Memory protocol operation failed: %s",
                type(exc).__name__,
            )

            return self._error_response(
                request=message,
                code="MEMORY_OPERATION_FAILED",
                safe_message="Memory operation failed.",
            )

    async def _list_memories(
        self,
        message: Message,
    ) -> Message:
        payload = self._payload(
            message
        )

        self._require_allowed_fields(
            payload,
            {
                "domain",
                "scope",
            },
        )

        domain = self._parse_optional_domain(
            payload.get("domain")
        )

        scope = self._parse_optional_scope(
            payload.get("scope")
        )

        self._validate_domain_scope_pair(
            domain,
            scope,
        )

        entries = await self._governance.list_memories(
            domain=domain,
            scope=scope,
        )

        visible_entries = tuple(
            entry
            for entry in entries
            if (
                entry.latest_revision.lifecycle
                is not MemoryLifecycle.DELETED
            )
        )

        return Message(
            type="memory.list.result",
            source="agent_core",
            payload={
                "request_id": message.id,
                "memories": [
                    self._serialize_entry(
                        entry
                    )
                    for entry in visible_entries
                ],
            },
        )

    async def _inspect_memory(
        self,
        message: Message,
    ) -> Message:
        memory_id = self._parse_memory_id_request(
            message
        )

        entry = await self._governance.inspect_memory(
            memory_id
        )

        return self._entry_response(
            request=message,
            response_type="memory.inspect.result",
            entry=entry,
        )

    async def _edit_memory(
        self,
        message: Message,
    ) -> Message:
        payload = self._payload(
            message
        )

        self._require_exact_fields(
            payload,
            {
                "memory_id",
                "content",
            },
        )

        memory_id = self._parse_memory_id(
            payload["memory_id"]
        )

        content = payload["content"]

        if (
            not isinstance(
                content,
                str,
            )
            or not content.strip()
        ):
            raise _MemoryProtocolRequestError(
                "content must be a non-empty string"
            )

        entry = await self._governance.edit_memory(
            memory_id,
            content,
        )

        return self._entry_response(
            request=message,
            response_type="memory.edit.result",
            entry=entry,
        )

    async def _delete_memory(
        self,
        message: Message,
    ) -> Message:
        memory_id = self._parse_memory_id_request(
            message
        )

        entry = await self._governance.delete_memory(
            memory_id
        )

        return self._entry_response(
            request=message,
            response_type="memory.delete.result",
            entry=entry,
        )

    async def _get_history(
        self,
        message: Message,
    ) -> Message:
        memory_id = self._parse_memory_id_request(
            message
        )

        revisions = await self._governance.get_history(
            memory_id
        )

        return Message(
            type="memory.history.result",
            source="agent_core",
            payload={
                "request_id": message.id,
                "memory_id": str(
                    memory_id
                ),
                "revisions": [
                    self._serialize_revision(
                        revision
                    )
                    for revision in revisions
                ],
            },
        )

    def _parse_memory_id_request(
        self,
        message: Message,
    ) -> UUID:
        payload = self._payload(
            message
        )

        self._require_exact_fields(
            payload,
            {
                "memory_id",
            },
        )

        return self._parse_memory_id(
            payload["memory_id"]
        )

    @staticmethod
    def _payload(
        message: Message,
    ) -> dict[str, Any]:
        if not isinstance(
            message.payload,
            dict,
        ):
            raise _MemoryProtocolRequestError(
                "payload must be an object"
            )

        return message.payload

    @staticmethod
    def _require_exact_fields(
        payload: dict[str, Any],
        expected: set[str],
    ) -> None:
        if set(payload) != expected:
            raise _MemoryProtocolRequestError(
                "invalid request fields"
            )

    @staticmethod
    def _require_allowed_fields(
        payload: dict[str, Any],
        allowed: set[str],
    ) -> None:
        if not set(payload).issubset(
            allowed
        ):
            raise _MemoryProtocolRequestError(
                "invalid request fields"
            )

    @staticmethod
    def _parse_memory_id(
        value: Any,
    ) -> UUID:
        if not isinstance(
            value,
            str,
        ):
            raise _MemoryProtocolRequestError(
                "memory_id must be a string"
            )

        try:
            return UUID(
                value
            )

        except ValueError as exc:
            raise _MemoryProtocolRequestError(
                "memory_id must be a UUID"
            ) from exc

    @staticmethod
    def _parse_optional_domain(
        value: Any,
    ) -> MemoryDomain | None:
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise _MemoryProtocolRequestError(
                "domain must be a string"
            )

        try:
            return MemoryDomain(
                value
            )

        except ValueError as exc:
            raise _MemoryProtocolRequestError(
                "unknown Memory domain"
            ) from exc

    @classmethod
    def _parse_optional_scope(
        cls,
        value: Any,
    ) -> MemoryScope | None:
        if value is None:
            return None

        if not isinstance(
            value,
            dict,
        ):
            raise _MemoryProtocolRequestError(
                "scope must be an object"
            )

        kind = value.get(
            "kind"
        )

        if not isinstance(
            kind,
            str,
        ):
            raise _MemoryProtocolRequestError(
                "scope.kind must be a string"
            )

        if kind == MemoryScopeKind.GLOBAL_USER.value:
            cls._require_allowed_fields(
                value,
                {
                    "kind",
                    "character_id",
                },
            )

            character_id = value.get(
                "character_id"
            )

            if character_id is not None:
                raise _MemoryProtocolRequestError(
                    "global_user scope cannot "
                    "define character_id"
                )

            return MemoryScope(
                kind=MemoryScopeKind.GLOBAL_USER,
            )

        if kind == MemoryScopeKind.CHARACTER.value:
            cls._require_exact_fields(
                value,
                {
                    "kind",
                    "character_id",
                },
            )

            character_id = value[
                "character_id"
            ]

            if (
                not isinstance(
                    character_id,
                    str,
                )
                or not character_id.strip()
            ):
                raise _MemoryProtocolRequestError(
                    "character scope requires "
                    "character_id"
                )

            return MemoryScope(
                kind=MemoryScopeKind.CHARACTER,
                character_id=character_id,
            )

        raise _MemoryProtocolRequestError(
            "unknown Memory scope kind"
        )


    @staticmethod
    def _validate_domain_scope_pair(
        domain: MemoryDomain | None,
        scope: MemoryScope | None,
    ) -> None:
        if domain is None or scope is None:
            return

        required_scope = (
            MemoryScopeKind.CHARACTER
            if domain is MemoryDomain.RELATIONSHIP
            else MemoryScopeKind.GLOBAL_USER
        )

        if scope.kind is not required_scope:
            raise _MemoryProtocolRequestError(
                "Memory domain and scope are incompatible"
            )


    @staticmethod
    def _serialize_entry(
        entry: MemoryGovernanceEntry,
    ) -> dict[str, Any]:
        memory = entry.memory

        return {
            "memory_id": str(
                memory.memory_id
            ),
            "domain": memory.domain.value,
            "scope": {
                "kind": memory.scope.kind.value,
                "character_id": (
                    memory.scope.character_id
                ),
            },
            "identity_key": (
                memory.identity_key.value
                if memory.identity_key is not None
                else None
            ),
            "latest_revision": (
                MemoryProtocolHandler
                ._serialize_revision(
                    entry.latest_revision
                )
            ),
        }

    @staticmethod
    def _serialize_revision(
        revision: MemoryRevision,
    ) -> dict[str, Any]:
        return {
            "revision_number": (
                revision.revision_number
            ),
            "content": revision.content,
            "source": revision.source.value,
            "lifecycle": (
                revision.lifecycle.value
            ),
            "recorded_at": (
                revision.recorded_at.isoformat()
            ),
            "occurred_at": (
                revision.occurred_at.isoformat()
                if revision.occurred_at is not None
                else None
            ),
        }

    @classmethod
    def _entry_response(
        cls,
        *,
        request: Message,
        response_type: str,
        entry: MemoryGovernanceEntry,
    ) -> Message:
        return Message(
            type=response_type,
            source="agent_core",
            payload={
                "request_id": request.id,
                "memory": cls._serialize_entry(
                    entry
                ),
            },
        )

    @staticmethod
    def _error_response(
        *,
        request: Message,
        code: str,
        safe_message: str,
    ) -> Message:
        return Message(
            type="error",
            source="agent_core",
            payload={
                "request_id": request.id,
                "code": code,
                "message": safe_message,
            },
        )
