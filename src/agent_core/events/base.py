from typing import Protocol, TypeVar

from agent_core.events.models import RuntimeEvent

TEvent = TypeVar(
    "TEvent",
    bound=RuntimeEvent,
    contravariant=True,
)


class EventPublisher(Protocol):
    """
    Runtime Event 发布能力的最小公共契约。

    普通事件生产者只依赖发布能力，
    不拥有 Event Bus 生命周期或订阅管理权限。
    """

    async def publish(
        self,
        event: RuntimeEvent,
    ) -> None:
        """
        发布一个 Runtime Event。
        """

        ...


class EventHandler(Protocol[TEvent]):
    """
    单一 Runtime Event 类型的异步订阅处理契约。
    """

    async def __call__(
        self,
        event: TEvent,
    ) -> None:
        """
        处理一个已路由的 Runtime Event。
        """

        ...
