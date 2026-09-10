import asyncio
from dataclasses import dataclass

import pytest

from agent_core.events import (
    EventBus,
    EventBusFullError,
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


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class OtherEvent(RuntimeEvent):
    value: str


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class DerivedExampleEvent(ExampleEvent):
    extra: str


def test_event_bus_rejects_non_positive_capacity() -> None:
    with pytest.raises(
        ValueError,
        match="queue_capacity must be positive",
    ):
        EventBus(
            queue_capacity=0,
        )

    with pytest.raises(
        ValueError,
        match="queue_capacity must be positive",
    ):
        EventBus(
            queue_capacity=-1,
        )


def test_event_bus_rejects_publish_before_start() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        event = ExampleEvent(
            source="tests.event_bus",
            value="example",
        )

        with pytest.raises(
            EventBusStateError,
            match="publish is only valid in RUNNING state",
        ):
            await bus.publish(
                event,
            )

    asyncio.run(
        scenario()
    )


def test_event_bus_rejects_second_start() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        await bus.start()

        with pytest.raises(
            EventBusStateError,
            match="start is only valid in NEW state",
        ):
            await bus.start()

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )


def test_event_bus_rejects_subscription_after_start() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        async def handler(
            event: ExampleEvent,
        ) -> None:
            del event

        await bus.start()

        with pytest.raises(
            EventBusStateError,
            match="subscriptions may only be registered before start",
        ):
            bus.subscribe(
                ExampleEvent,
                handler,
            )

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )


def test_event_bus_routes_by_exact_type() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=4,
        )

        received: list[RuntimeEvent] = []
        handled = asyncio.Event()

        async def handler(
            event: ExampleEvent,
        ) -> None:
            received.append(
                event,
            )
            handled.set()

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        matching_event = ExampleEvent(
            source="tests.event_bus",
            value="matching",
        )

        await bus.publish(
            matching_event,
        )

        await handled.wait()

        assert received == [
            matching_event,
        ]

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )


def test_event_bus_does_not_use_inheritance_routing() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=4,
        )

        received: list[RuntimeEvent] = []

        async def handler(
            event: ExampleEvent,
        ) -> None:
            received.append(
                event,
            )

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        derived_event = DerivedExampleEvent(
            source="tests.event_bus",
            value="derived",
            extra="extra",
        )

        await bus.publish(
            derived_event,
        )

        await bus._queue.join()

        assert received == []

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )


def test_event_bus_preserves_duplicate_explicit_subscriptions() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=4,
        )

        received: list[ExampleEvent] = []

        async def handler(
            event: ExampleEvent,
        ) -> None:
            received.append(
                event,
            )

        bus.subscribe(
            ExampleEvent,
            handler,
        )
        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        event = ExampleEvent(
            source="tests.event_bus",
            value="duplicate",
        )

        await bus.publish(
            event,
        )

        await bus._queue.join()

        assert received == [
            event,
            event,
        ]

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )


def test_publish_returns_before_handler_completion() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=2,
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

        event = ExampleEvent(
            source="tests.event_bus",
            value="example",
        )

        await bus.publish(
            event,
        )

        await handler_started.wait()

        assert not release_handler.is_set()

        release_handler.set()

        await bus._queue.join()

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )


def test_event_bus_dispatches_in_queue_admission_order() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=4,
        )

        received: list[str] = []

        async def handler(
            event: ExampleEvent,
        ) -> None:
            received.append(
                event.value,
            )

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus",
                value="first",
            )
        )
        await bus.publish(
            ExampleEvent(
                source="tests.event_bus",
                value="second",
            )
        )
        await bus.publish(
            ExampleEvent(
                source="tests.event_bus",
                value="third",
            )
        )

        await bus._queue.join()

        assert received == [
            "first",
            "second",
            "third",
        ]

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )


def test_full_queue_rejects_publication_explicitly() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        first_handler_started = asyncio.Event()
        release_first_handler = asyncio.Event()

        async def handler(
            event: ExampleEvent,
        ) -> None:
            if event.value == "first":
                first_handler_started.set()
                await release_first_handler.wait()

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus",
                value="first",
            )
        )

        await first_handler_started.wait()

        second_event = ExampleEvent(
            source="tests.event_bus",
            value="second",
        )

        await bus.publish(
            second_event,
        )

        third_event = ExampleEvent(
            source="tests.event_bus",
            value="third",
        )

        with pytest.raises(
            EventBusFullError,
            match="queue is full",
        ):
            await bus.publish(
                third_event,
            )

        release_first_handler.set()

        await bus._queue.join()

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )

def test_reentrant_publish_fails_fast_when_queue_is_full() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        first_handler_started = asyncio.Event()
        allow_reentrant_publish = asyncio.Event()
        reentrant_publish_finished = asyncio.Event()

        overload_errors: list[EventBusFullError] = []
        received: list[str] = []

        async def handler(
            event: ExampleEvent,
        ) -> None:
            received.append(
                event.value,
            )

            if event.value != "first":
                return

            first_handler_started.set()
            await allow_reentrant_publish.wait()

            derived_event = ExampleEvent(
                source="tests.event_bus.handler",
                value="derived",
            )

            try:
                await bus.publish(
                    derived_event,
                )
            except EventBusFullError as error:
                overload_errors.append(
                    error,
                )
            finally:
                reentrant_publish_finished.set()

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus",
                value="first",
            )
        )

        await first_handler_started.wait()

        await bus.publish(
            ExampleEvent(
                source="tests.event_bus",
                value="second",
            )
        )

        allow_reentrant_publish.set()

        await asyncio.wait_for(
            reentrant_publish_finished.wait(),
            timeout=1.0,
        )

        await bus._queue.join()

        assert len(overload_errors) == 1
        assert received == [
            "first",
            "second",
        ]

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )


def test_zero_subscriber_event_completes_normally() -> None:
    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        await bus.start()

        await bus.publish(
            OtherEvent(
                source="tests.event_bus",
                value="ignored",
            )
        )

        await bus._queue.join()

        assert bus._dispatcher_task is not None
        bus._dispatcher_task.cancel()

        with pytest.raises(
            asyncio.CancelledError,
        ):
            await bus._dispatcher_task

    asyncio.run(
        scenario()
    )
