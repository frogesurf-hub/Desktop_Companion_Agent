from dataclasses import FrozenInstanceError
from datetime import (
    UTC,
    datetime,
    timedelta,
    timezone,
)

import pytest

from agent_core.temporal import (
    Clock,
    SystemClock,
    TemporalContext,
)
from agent_core.tests.fakes import FixedClock


def test_system_clock_returns_timezone_aware_datetime() -> None:
    """
    验证生产 Clock 返回 timezone-aware datetime。
    """

    clock: Clock = SystemClock()

    current_datetime = clock.now()

    assert current_datetime.tzinfo is not None
    assert current_datetime.utcoffset() is not None


def test_fixed_clock_satisfies_clock_contract() -> None:
    """
    验证测试可以通过 Clock contract 控制当前时间。
    """

    expected = datetime(
        2026,
        9,
        13,
        1,
        30,
        tzinfo=timezone(
            timedelta(hours=8),
        ),
    )

    clock: Clock = FixedClock(
        expected,
    )

    assert clock.now() == expected


def test_temporal_context_preserves_aware_datetime() -> None:
    """
    验证 TemporalContext 保留 Clock 提供的时间快照。
    """

    current_datetime = datetime(
        2026,
        9,
        13,
        1,
        30,
        tzinfo=timezone(
            timedelta(hours=8),
        ),
    )

    context = TemporalContext(
        current_datetime=current_datetime,
    )

    assert context.current_datetime == current_datetime


def test_temporal_context_derives_date_weekday_and_offset() -> None:
    """
    验证派生 temporal 信息全部来自同一个时间快照。
    """

    context = TemporalContext(
        current_datetime=datetime(
            2026,
            9,
            13,
            1,
            30,
            tzinfo=timezone(
                timedelta(hours=8),
            ),
        ),
    )

    assert context.current_date.isoformat() == "2026-09-13"
    assert context.weekday_name == "Sunday"
    assert context.utc_offset == timedelta(hours=8)


def test_temporal_context_rejects_naive_datetime() -> None:
    """
    验证没有 timezone 的 datetime 不能成为 Runtime temporal truth。
    """

    with pytest.raises(
        ValueError,
        match="must be timezone-aware",
    ):
        TemporalContext(
            current_datetime=datetime(
                2026,
                9,
                13,
                1,
                30,
            ),
        )


def test_temporal_context_is_immutable() -> None:
    """
    验证一次请求的 TemporalContext 创建后不会变化。
    """

    context = TemporalContext(
        current_datetime=datetime(
            2026,
            9,
            13,
            1,
            30,
            tzinfo=UTC,
        ),
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        setattr(
            context,
            "current_datetime",
            datetime.now(UTC),
        )
