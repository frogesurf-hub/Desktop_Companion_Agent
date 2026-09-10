import asyncio
from collections import defaultdict
from enum import Enum, auto
from typing import TypeVar, cast

from agent_core.events.base import EventHandler
from agent_core.events.errors import (
    EventBusFullError,
    EventBusStateError,
)
from agent_core.events.models import RuntimeEvent

TEvent = TypeVar(
    "TEvent",
    bound=RuntimeEvent,
)


class _EventBusState(Enum):
    NEW = auto()
    RUNNING = auto()
    CLOSING = auto()
    CLOSED = auto()


class EventBus:
    """
    Runtime Event 的异步进程内总线。

    Task 2 建立 bounded queue、静态订阅、exact-type routing
    与 fail-fast queue-admission publish 语义。

    完整 shutdown、failure isolation 与 cancellation
    将在 Task 3 中完成。
    """

    def __init__(
        self,
        *,
        queue_capacity: int,
    ) -> None:
        if queue_capacity <= 0:
            raise ValueError(
                "EventBus queue_capacity must be positive"
            )

        self._queue: asyncio.Queue[RuntimeEvent] = asyncio.Queue(
            maxsize=queue_capacity,
        )

        self._subscriptions: dict[
            type[RuntimeEvent],
            list[EventHandler[RuntimeEvent]],
        ] = defaultdict(list)

        self._state = _EventBusState.NEW
        self._dispatcher_task: asyncio.Task[None] | None = None

    def subscribe(
        self,
        event_type: type[TEvent],
        handler: EventHandler[TEvent],
    ) -> None:
        """
        在 Event Bus 启动前注册 exact-type subscriber。
        """

        if self._state is not _EventBusState.NEW:
            raise EventBusStateError(
                "EventBus subscriptions may only be registered before start"
            )

        erased_handler = cast(
            EventHandler[RuntimeEvent],
            handler,
        )

        self._subscriptions[event_type].append(
            erased_handler,
        )

    async def start(self) -> None:
        """
        启动唯一 dispatcher。
        """

        if self._state is not _EventBusState.NEW:
            raise EventBusStateError(
                "EventBus start is only valid in NEW state"
            )

        self._state = _EventBusState.RUNNING

        self._dispatcher_task = asyncio.create_task(
            self._dispatch_loop(),
            name="event-bus-dispatcher",
        )

    async def publish(
        self,
        event: RuntimeEvent,
    ) -> None:
        """
        尝试将 Event 接受到 bounded queue。

        返回只代表 queue admission 成功，
        不代表 subscriber 已经开始或完成。

        Queue 满时立即失败，不等待未来容量。
        """

        if self._state is not _EventBusState.RUNNING:
            raise EventBusStateError(
                "EventBus publish is only valid in RUNNING state"
            )

        try:
            self._queue.put_nowait(
                event,
            )
        except asyncio.QueueFull:
            raise EventBusFullError(
                "EventBus queue is full"
            ) from None

    async def _dispatch_loop(self) -> None:
        """
        按 queue admission 顺序持续 dispatch Event。
        """

        while True:
            event = await self._queue.get()

            try:
                await self._dispatch(
                    event,
                )
            finally:
                self._queue.task_done()

    async def _dispatch(
        self,
        event: RuntimeEvent,
    ) -> None:
        """
        将 Event 路由给其 exact concrete type 的 subscribers。

        Task 2 暂时顺序执行 subscriber；
        Task 3 将实现正式的并发与 failure isolation 契约。
        """

        handlers = self._subscriptions.get(
            type(event),
            (),
        )

        for handler in handlers:
            await handler(
                event,
            )
