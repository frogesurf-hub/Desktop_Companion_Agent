from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from agent_core.events import RuntimeEvent


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class ExampleRuntimeEvent(RuntimeEvent):
    """
    Event System 基础契约测试使用的业务无关事件。
    """

    detail: str


def test_runtime_event_generates_identity_and_utc_timestamp() -> None:
    """
    验证默认创建会生成独立 UUID 和当前 UTC 时间。
    """

    before = datetime.now(UTC)

    first_event = ExampleRuntimeEvent(
        source="tests.event_models",
        detail="first",
    )
    second_event = ExampleRuntimeEvent(
        source="tests.event_models",
        detail="second",
    )

    after = datetime.now(UTC)

    assert isinstance(
        first_event.event_id,
        UUID,
    )
    assert first_event.event_id != second_event.event_id

    assert before <= first_event.occurred_at <= after
    assert first_event.occurred_at.tzinfo is UTC


def test_runtime_event_normalizes_aware_timestamp_to_utc() -> None:
    """
    验证带时区时间会在 Event 边界规范化为 UTC。
    """

    utc_plus_eight = timezone(
        timedelta(hours=8),
    )

    occurred_at = datetime(
        2026,
        9,
        10,
        8,
        30,
        tzinfo=utc_plus_eight,
    )

    event = ExampleRuntimeEvent(
        source="tests.event_models",
        occurred_at=occurred_at,
        detail="example",
    )

    assert event.occurred_at == datetime(
        2026,
        9,
        10,
        0,
        30,
        tzinfo=UTC,
    )


def test_runtime_event_rejects_naive_timestamp() -> None:
    """
    验证 Runtime Event 不接受无时区时间。
    """

    with pytest.raises(
        ValueError,
        match="occurred_at must be timezone-aware",
    ):
        ExampleRuntimeEvent(
            source="tests.event_models",
            occurred_at=datetime(
                2026,
                9,
                10,
                0,
                30,
            ),
            detail="example",
        )


def test_runtime_event_rejects_blank_source() -> None:
    """
    验证 Runtime Event source 必须是非空逻辑标识。
    """

    with pytest.raises(
        ValueError,
        match="source must not be empty",
    ):
        ExampleRuntimeEvent(
            source="   ",
            detail="example",
        )


def test_runtime_event_preserves_explicit_causal_metadata() -> None:
    """
    验证显式注入的身份与因果元数据保持不变。
    """

    event_id = uuid4()
    correlation_id = uuid4()
    causation_id = uuid4()

    occurred_at = datetime(
        2026,
        9,
        10,
        tzinfo=UTC,
    )

    event = ExampleRuntimeEvent(
        source="tests.event_models",
        event_id=event_id,
        occurred_at=occurred_at,
        correlation_id=correlation_id,
        causation_id=causation_id,
        detail="example",
    )

    assert event.event_id == event_id
    assert event.occurred_at == occurred_at
    assert event.correlation_id == correlation_id
    assert event.causation_id == causation_id


def test_runtime_event_is_immutable() -> None:
    """
    验证 Runtime Event 及具体 Event 字段不可原地修改。
    """

    event = ExampleRuntimeEvent(
        source="tests.event_models",
        detail="original",
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        setattr(
            event,
            "detail",
            "changed",
        )
