import asyncio
from dataclasses import dataclass

from agent_core.events import (
    EventHandler,
    EventPublisher,
    RuntimeEvent,
)


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class ExampleRuntimeEvent(RuntimeEvent):
    """
    Event System 公共契约测试使用的业务无关事件。
    """

    detail: str


class RecordingEventPublisher:
    """
    测试专用的确定性 EventPublisher。
    """

    def __init__(self) -> None:
        self.events: list[RuntimeEvent] = []

    async def publish(
        self,
        event: RuntimeEvent,
    ) -> None:
        """
        记录收到的 Runtime Event。
        """

        self.events.append(
            event,
        )


def _as_event_publisher(
    publisher: EventPublisher,
) -> EventPublisher:
    """
    为静态类型检查提供显式 EventPublisher 边界。
    """

    return publisher


def _as_event_handler(
    handler: EventHandler[ExampleRuntimeEvent],
) -> EventHandler[ExampleRuntimeEvent]:
    """
    为静态类型检查提供显式 EventHandler 边界。
    """

    return handler


def test_recording_publisher_satisfies_event_publisher_contract() -> None:
    """
    验证普通对象可以通过结构化类型满足最小发布契约。
    """

    recording_publisher = RecordingEventPublisher()

    publisher = _as_event_publisher(
        recording_publisher,
    )

    event = ExampleRuntimeEvent(
        source="tests.event_contract",
        detail="example",
    )

    asyncio.run(
        publisher.publish(
            event,
        )
    )

    assert recording_publisher.events == [
        event,
    ]


def test_async_function_satisfies_event_handler_contract() -> None:
    """
    验证 async callable 可以满足 EventHandler 契约。
    """

    received: list[ExampleRuntimeEvent] = []

    async def handler(
        event: ExampleRuntimeEvent,
    ) -> None:
        received.append(
            event,
        )

    typed_handler = _as_event_handler(
        handler,
    )

    event = ExampleRuntimeEvent(
        source="tests.event_contract",
        detail="example",
    )

    asyncio.run(
        typed_handler(
            event,
        )
    )

    assert received == [
        event,
    ]
