import asyncio
from dataclasses import dataclass

import pytest

from agent_core.events import (
    EventBus,
    EventBusStateError,
    RuntimeEvent,
)


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class ExampleEvent(RuntimeEvent):
    value: str


class FailingDispatchEventBus(EventBus):
    """
    测试 dispatcher infrastructure failure 的 EventBus。
    """

    async def _dispatch(
        self,
        event: RuntimeEvent,
    ) -> None:
        del event
        raise RuntimeError(
            "forced dispatcher failure"
        )


def test_sibling_subscribers_run_concurrently() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=2,
        )

        first_started = asyncio.Event()
        second_started = asyncio.Event()
        release_handlers = asyncio.Event()

        async def first_handler(
            event: ExampleEvent,
        ) -> None:
            del event
            first_started.set()
            await release_handlers.wait()

        async def second_handler(
            event: ExampleEvent,
        ) -> None:
            del event
            second_started.set()
            await release_handlers.wait()

        bus.subscribe(
            ExampleEvent,
            first_handler,
        )
        bus.subscribe(
            ExampleEvent,
            second_handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="example",
            )
        )

        await asyncio.wait_for(
            asyncio.gather(
                first_started.wait(),
                second_started.wait(),
            ),
            timeout=1.0,
        )

        release_handlers.set()

        await bus.close()

    asyncio.run(
        scenario()
    )


def test_next_event_waits_for_current_subscribers_to_settle() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=2,
        )

        first_started = asyncio.Event()
        release_first = asyncio.Event()
        second_started = asyncio.Event()

        async def handler(
            event: ExampleEvent,
        ) -> None:
            if event.value == "first":
                first_started.set()
                await release_first.wait()
                return

            if event.value == "second":
                second_started.set()

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="first",
            )
        )

        await first_started.wait()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="second",
            )
        )

        await asyncio.sleep(0)

        assert not second_started.is_set()

        release_first.set()

        await asyncio.wait_for(
            second_started.wait(),
            timeout=1.0,
        )

        await bus.close()

    asyncio.run(
        scenario()
    )


def test_ordinary_subscriber_failure_is_isolated_and_future_events_continue() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=2,
        )

        failing_calls: list[str] = []
        received: list[str] = []

        async def failing_handler(
            event: ExampleEvent,
        ) -> None:
            failing_calls.append(
                event.value,
            )
            raise RuntimeError(
                "expected subscriber failure"
            )

        async def healthy_handler(
            event: ExampleEvent,
        ) -> None:
            received.append(
                event.value,
            )

        bus.subscribe(
            ExampleEvent,
            failing_handler,
        )
        bus.subscribe(
            ExampleEvent,
            healthy_handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="first",
            )
        )

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="second",
            )
        )

        await bus.close()

        assert failing_calls == [
            "first",
            "second",
        ]

        assert received == [
            "first",
            "second",
        ]

    asyncio.run(
        scenario()
    )


def test_close_drains_accepted_events_and_rejects_new_publication() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=2,
        )

        first_started = asyncio.Event()
        release_first = asyncio.Event()

        received: list[str] = []

        async def handler(
            event: ExampleEvent,
        ) -> None:
            received.append(
                event.value,
            )

            if event.value == "first":
                first_started.set()
                await release_first.wait()

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="first",
            )
        )

        await first_started.wait()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="second",
            )
        )

        close_task = asyncio.create_task(
            bus.close()
        )

        await asyncio.sleep(0)

        assert not close_task.done()

        with pytest.raises(
            EventBusStateError,
            match="publish is only valid in RUNNING state",
        ):
            await bus.publish(
                ExampleEvent(
                    source="tests.event_bus_lifecycle",
                    value="third",
                )
            )

        release_first.set()

        await asyncio.wait_for(
            close_task,
            timeout=1.0,
        )

        assert received == [
            "first",
            "second",
        ]

    asyncio.run(
        scenario()
    )


def test_concurrent_and_repeated_close_are_idempotent() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        handler_started = asyncio.Event()
        release_handler = asyncio.Event()

        async def handler(
            event: ExampleEvent,
        ) -> None:
            del event
            handler_started.set()
            await release_handler.wait()

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="example",
            )
        )

        await handler_started.wait()

        first_close = asyncio.create_task(
            bus.close()
        )

        await asyncio.sleep(0)

        second_close = asyncio.create_task(
            bus.close()
        )

        await asyncio.sleep(0)

        assert not first_close.done()
        assert not second_close.done()

        release_handler.set()

        await asyncio.wait_for(
            asyncio.gather(
                first_close,
                second_close,
            ),
            timeout=1.0,
        )

        # CLOSED -> close() 仍然是幂等操作。
        await bus.close()

    asyncio.run(
        scenario()
    )


def test_close_from_new_is_terminal() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        await bus.close()

        # CLOSED -> close() 再次调用正常返回。
        await bus.close()

        with pytest.raises(
            EventBusStateError,
            match="start is only valid in NEW state",
        ):
            await bus.start()

        with pytest.raises(
            EventBusStateError,
            match="publish is only valid in RUNNING state",
        ):
            await bus.publish(
                ExampleEvent(
                    source="tests.event_bus_lifecycle",
                    value="example",
                )
            )

        async def handler(
            event: ExampleEvent,
        ) -> None:
            del event

        with pytest.raises(
            EventBusStateError,
            match="subscriptions may only be registered before start",
        ):
            bus.subscribe(
                ExampleEvent,
                handler,
            )

    asyncio.run(
        scenario()
    )


def test_cancelled_close_forces_terminal_cleanup() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=2,
        )

        handler_started = asyncio.Event()
        handler_finished = asyncio.Event()
        never_release = asyncio.Event()

        async def handler(
            event: ExampleEvent,
        ) -> None:
            del event
            handler_started.set()

            try:
                await never_release.wait()
            finally:
                handler_finished.set()

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="first",
            )
        )

        await handler_started.wait()

        # 保留一个已经 accepted 但尚未 dispatch 的 Event，
        # 用于验证 forced cleanup 的 queue accounting。
        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="second",
            )
        )

        close_task = asyncio.create_task(
            bus.close()
        )

        await asyncio.sleep(0)

        close_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await close_task

        await asyncio.wait_for(
            handler_finished.wait(),
            timeout=1.0,
        )

        # forced cleanup 后 unfinished-task accounting 必须归零。
        await asyncio.wait_for(
            bus._queue.join(),
            timeout=1.0,
        )

        with pytest.raises(
            EventBusStateError,
        ):
            await bus.publish(
                ExampleEvent(
                    source="tests.event_bus_lifecycle",
                    value="third",
                )
            )

        await bus.close()

    asyncio.run(
        scenario()
    )


def test_subscriber_cancellation_cancels_siblings_and_terminates_bus() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        cancelling_started = asyncio.Event()
        sibling_started = asyncio.Event()
        allow_cancellation = asyncio.Event()
        sibling_finished = asyncio.Event()
        sibling_block = asyncio.Event()

        async def cancelling_handler(
            event: ExampleEvent,
        ) -> None:
            del event
            cancelling_started.set()

            await allow_cancellation.wait()

            raise asyncio.CancelledError

        async def sibling_handler(
            event: ExampleEvent,
        ) -> None:
            del event
            sibling_started.set()

            try:
                await sibling_block.wait()
            finally:
                sibling_finished.set()

        bus.subscribe(
            ExampleEvent,
            cancelling_handler,
        )
        bus.subscribe(
            ExampleEvent,
            sibling_handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="example",
            )
        )

        await asyncio.wait_for(
            asyncio.gather(
                cancelling_started.wait(),
                sibling_started.wait(),
            ),
            timeout=1.0,
        )

        allow_cancellation.set()

        dispatcher_task = bus._dispatcher_task

        assert dispatcher_task is not None

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await asyncio.wait_for(
                dispatcher_task,
                timeout=1.0,
            )

        await asyncio.wait_for(
            sibling_finished.wait(),
            timeout=1.0,
        )

        # 让 done callback 完成 terminal state transition。
        await asyncio.sleep(0)

        with pytest.raises(
            EventBusStateError,
        ):
            await bus.publish(
                ExampleEvent(
                    source="tests.event_bus_lifecycle",
                    value="later",
                )
            )

    asyncio.run(
        scenario()
    )


def test_unexpected_dispatcher_failure_is_terminal_and_cleans_queue() -> None:
    async def scenario() -> None:
        bus = FailingDispatchEventBus(
            queue_capacity=2,
        )

        await bus.start()

        # publish() 当前没有 suspension point，
        # 因此两个 Event 都会先进入 queue，
        # dispatcher 随后才获得执行机会。
        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="first",
            )
        )

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus_lifecycle",
                value="second",
            )
        )

        await asyncio.wait_for(
            bus._closed_event.wait(),
            timeout=1.0,
        )

        dispatcher_task = bus._dispatcher_task

        assert dispatcher_task is not None

        with pytest.raises(
            RuntimeError,
            match="forced dispatcher failure",
        ):
            await dispatcher_task

        # terminal cleanup 必须正确平衡 Queue bookkeeping。
        await asyncio.wait_for(
            bus._queue.join(),
            timeout=1.0,
        )

        with pytest.raises(
            EventBusStateError,
        ):
            await bus.publish(
                ExampleEvent(
                    source="tests.event_bus_lifecycle",
                    value="later",
                )
            )

        # EventBus 已 terminal，重复 close 正常完成。
        await bus.close()

    asyncio.run(
        scenario()
    )
