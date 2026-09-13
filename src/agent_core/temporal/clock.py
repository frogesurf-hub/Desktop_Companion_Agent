from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """
    Agent Runtime 的真实时间查询边界。

    实现必须返回 timezone-aware datetime。
    """

    def now(self) -> datetime:
        """
        返回当前真实时间。
        """

        ...


class SystemClock:
    """
    基于操作系统本地时间的生产 Clock。
    """

    def now(self) -> datetime:
        """
        返回 timezone-aware 的当前本地时间。
        """

        return datetime.now().astimezone()
