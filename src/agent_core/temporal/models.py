from dataclasses import dataclass
from datetime import date, datetime, timedelta

_WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class TemporalContext:
    """
    单次 Runtime 请求使用的真实时间快照。

    时间来源由 Clock 提供；
    TemporalContext 本身不查询系统时间。
    """

    current_datetime: datetime

    def __post_init__(self) -> None:
        """
        保证 Runtime temporal truth 使用 timezone-aware datetime。
        """

        if (
            self.current_datetime.tzinfo is None
            or self.current_datetime.utcoffset() is None
        ):
            raise ValueError(
                "TemporalContext current_datetime "
                "must be timezone-aware"
            )

    @property
    def current_date(self) -> date:
        """
        返回当前本地日期。
        """

        return self.current_datetime.date()

    @property
    def weekday_name(self) -> str:
        """
        返回与当前日期对应的稳定英文星期名称。

        不依赖操作系统 locale。
        """

        return _WEEKDAY_NAMES[
            self.current_datetime.weekday()
        ]

    @property
    def utc_offset(self) -> timedelta:
        """
        返回当前时间相对 UTC 的偏移。
        """

        offset = self.current_datetime.utcoffset()

        if offset is None:
            raise RuntimeError(
                "TemporalContext lost timezone awareness"
            )

        return offset
