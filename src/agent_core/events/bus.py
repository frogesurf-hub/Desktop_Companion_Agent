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

    Event Bus 提供：

    - bounded fail-fast queue admission；
    - static exact-type subscriptions；
    - single-dispatcher FIFO Event processing；
    - concurrent sibling subscribers；
    - ordinary subscriber failure isolation；
    - explicit lifecycle and graceful shutdown。
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

        self._closed_event = asyncio.Event()

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

        dispatcher_task = asyncio.create_task(
            self._dispatch_loop(),
            name="event-bus-dispatcher",
        )

        self._dispatcher_task = dispatcher_task

        dispatcher_task.add_done_callback(
            self._on_dispatcher_done,
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

    async def close(self) -> None:
        """
        关闭 Event Bus。

        RUNNING 状态执行 graceful drain。
        重复调用 close 是幂等的。

        如果 graceful close 本身被外部取消，
        Event Bus 会强制终止 dispatcher 并完成 terminal cleanup，
        然后继续向调用者传播 cancellation。
        """

        if self._state is _EventBusState.CLOSED:
            return

        if self._state is _EventBusState.NEW:
            self._mark_closed()
            return

        if self._state is _EventBusState.CLOSING:
            await self._closed_event.wait()
            return

        self._state = _EventBusState.CLOSING

        try:
            await self._queue.join()
            await self._stop_dispatcher()
        except asyncio.CancelledError:
            await self._force_terminal_cleanup()
            raise
        finally:
            self._mark_closed()

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
        并发执行当前 Event 的所有 exact-type subscribers。

        当前 Event 的 subscriber 全部 settle 后，
        dispatcher 才会处理下一个 Event。
        """

        handlers = self._subscriptions.get(
            type(event),
            (),
        )

        if not handlers:
            return

        tasks = [
            asyncio.create_task(
                self._run_handler(
                    handler,
                    event,
                )
            )
            for handler in handlers
        ]

        try:
            await asyncio.gather(
                *tasks,
            )
        except BaseException:
            for task in tasks:
                if not task.done():
                    task.cancel()

            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

            raise

    async def _run_handler(
        self,
        handler: EventHandler[RuntimeEvent],
        event: RuntimeEvent,
    ) -> None:
        """
        执行单个 subscriber 的隔离边界。

        普通 Exception 在 subscriber 边界被隔离。
        Cancellation 和其他 BaseException 保持终止语义。
        """

        try:
            await handler(
                event,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            # Task 4 将在此边界增加安全 failure observability。
            return

    async def _stop_dispatcher(self) -> None:
        """
        停止并回收 private dispatcher task。
        """

        dispatcher_task = self._dispatcher_task

        if dispatcher_task is None:
            return

        if not dispatcher_task.done():
            dispatcher_task.cancel()

        try:
            await dispatcher_task
        except asyncio.CancelledError:
            pass
        except Exception:
            # Unexpected dispatcher failure is terminal.
            # Task 4 will add safe diagnostics at this boundary.
            pass

    async def _force_terminal_cleanup(self) -> None:
        """
        强制终止 Event Bus 并清理仍然 accepted 的待处理 Event。

        仅用于 graceful shutdown 被取消或 dispatcher
        已无法继续正常处理 accepted work 的 terminal path。
        """

        try:
            await self._stop_dispatcher()
        finally:
            self._discard_pending_events()
            self._mark_closed()

    def _on_dispatcher_done(
        self,
        task: asyncio.Task[None],
    ) -> None:
        """
        处理 private dispatcher 的 terminal completion。

        Event Bus 不自动 restart dispatcher。
        """

        if not task.cancelled():
            task.exception()

        if self._state in (
            _EventBusState.RUNNING,
            _EventBusState.CLOSING,
        ):
            self._discard_pending_events()
            self._mark_closed()

    def _discard_pending_events(self) -> None:
        """
        清理 terminal path 中无法继续 dispatch 的 queued Events。

        每个从 Queue 移除的 Event 都必须匹配一次 task_done，
        以保证 Queue unfinished-task accounting 正确结束。
        """

        while True:
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            else:
                self._queue.task_done()

    def _mark_closed(self) -> None:
        """
        将 Event Bus 标记为 terminal CLOSED。
        """

        self._state = _EventBusState.CLOSED
        self._closed_event.set()
