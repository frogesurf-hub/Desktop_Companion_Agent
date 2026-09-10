import asyncio
import logging
from dataclasses import dataclass

from agent_core.events import (
    EventBus,
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
    observability 娴嬭瘯浣跨敤鐨?infrastructure-failure EventBus銆?
    """

    async def _dispatch(
        self,
        event: RuntimeEvent,
    ) -> None:
        del event
        raise RuntimeError(
            "PRIVATE_DISPATCH_FAILURE_MESSAGE"
        )


def test_event_bus_lifecycle_logs_start_and_close(
    caplog,
) -> None:
    caplog.set_level(
        logging.DEBUG,
        logger="agent_core.events.bus",
    )

    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=4,
        )

        await bus.start()
        await bus.close()

    asyncio.run(
        scenario()
    )

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "agent_core.events.bus"
    ]

    assert any(
        "event_bus_started" in message
        and "queue_capacity=4" in message
        for message in messages
    )

    assert any(
        "event_bus_closing" in message
        for message in messages
    )

    assert any(
        "event_bus_closed" in message
        and "previous_state=CLOSING" in message
        for message in messages
    )


def test_event_lifecycle_logs_traceable_metadata_and_handler_duration(
    caplog,
) -> None:
    caplog.set_level(
        logging.DEBUG,
        logger="agent_core.events.bus",
    )

    async def scenario() -> ExampleEvent:
        bus = EventBus(
            queue_capacity=2,
        )

        async def handler(
            event: ExampleEvent,
        ) -> None:
            del event

        bus.subscribe(
            ExampleEvent,
            handler,
        )

        await bus.start()

        event = ExampleEvent(
            source="tests.event_observability",
            value="ordinary-value",
        )

        await bus.publish(
            event,
        )

        await bus.close()

        return event

    event = asyncio.run(
        scenario()
    )

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "agent_core.events.bus"
    ]

    event_id = str(
        event.event_id,
    )

    assert any(
        "stage=accepted" in message
        and event_id in message
        and "source=tests.event_observability" in message
        and "event_type=" in message
        for message in messages
    )

    assert any(
        "stage=dispatch_started" in message
        and event_id in message
        for message in messages
    )

    assert any(
        "handler_lifecycle stage=completed" in message
        and event_id in message
        and "handler=" in message
        and "duration_ms=" in message
        for message in messages
    )

    assert any(
        "stage=dispatch_completed" in message
        and event_id in message
        and "duration_ms=" in message
        for message in messages
    )


def test_subscriber_failure_is_diagnosable_without_sensitive_content(
    caplog,
) -> None:
    caplog.set_level(
        logging.DEBUG,
        logger="agent_core.events.bus",
    )

    sensitive_payload = "PRIVATE_EVENT_PAYLOAD_MARKER"
    sensitive_error = "PRIVATE_EXCEPTION_MESSAGE_MARKER"

    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        async def failing_handler(
            event: ExampleEvent,
        ) -> None:
            del event
            raise RuntimeError(
                sensitive_error
            )

        bus.subscribe(
            ExampleEvent,
            failing_handler,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_observability",
                value=sensitive_payload,
            )
        )

        await bus.close()

    asyncio.run(
        scenario()
    )

    records = [
        record
        for record in caplog.records
        if record.name == "agent_core.events.bus"
    ]

    messages = [
        record.getMessage()
        for record in records
    ]

    assert any(
        record.levelno == logging.ERROR
        and "handler_lifecycle stage=failed"
        in record.getMessage()
        and "exception_type=builtins.RuntimeError"
        in record.getMessage()
        for record in records
    )

    combined_logs = "\n".join(
        messages,
    )

    assert sensitive_payload not in combined_logs
    assert sensitive_error not in combined_logs


def test_unexpected_dispatcher_failure_is_logged_without_exception_message(
    caplog,
) -> None:
    caplog.set_level(
        logging.DEBUG,
        logger="agent_core.events.bus",
    )

    async def scenario() -> None:
        bus = FailingDispatchEventBus(
            queue_capacity=1,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.event_observability",
                value="ordinary-value",
            )
        )

        await asyncio.wait_for(
            bus._closed_event.wait(),
            timeout=1.0,
        )

        dispatcher_task = bus._dispatcher_task

        assert dispatcher_task is not None

        try:
            await dispatcher_task
        except RuntimeError:
            pass

        await bus.close()

    asyncio.run(
        scenario()
    )

    records = [
        record
        for record in caplog.records
        if record.name == "agent_core.events.bus"
    ]

    messages = [
        record.getMessage()
        for record in records
    ]

    assert any(
        record.levelno == logging.ERROR
        and "event_bus_dispatcher_terminal"
        in record.getMessage()
        and "reason=exception"
        in record.getMessage()
        and "exception_type=builtins.RuntimeError"
        in record.getMessage()
        for record in records
    )

    combined_logs = "\n".join(
        messages,
    )

    assert "PRIVATE_DISPATCH_FAILURE_MESSAGE" not in combined_logs


def test_event_source_newlines_are_sanitized_in_logs(
    caplog,
) -> None:
    caplog.set_level(
        logging.DEBUG,
        logger="agent_core.events.bus",
    )

    async def scenario() -> None:
        bus = EventBus(
            queue_capacity=1,
        )

        await bus.start()

        await bus.publish(
            ExampleEvent(
                source="tests.source\r\ninjected_line",
                value="ordinary-value",
            )
        )

        await bus.close()

    asyncio.run(
        scenario()
    )

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "agent_core.events.bus"
    ]

    accepted_message = next(
        message
        for message in messages
        if "stage=accepted" in message
    )

    assert "source=tests.source\\r\\ninjected_line" in accepted_message
    assert "tests.source\r\ninjected_line" not in accepted_message
