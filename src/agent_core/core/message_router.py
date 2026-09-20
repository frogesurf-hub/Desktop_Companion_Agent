from typing import Protocol

from agent_core.core.message import Message


class MessageProcessor(Protocol):
    """
    Runtime request/response capability boundary.
    """

    async def process_message(
        self,
        message: Message,
    ) -> Message:
        ...


class RuntimeMessageRouter:
    """
    将协议 Message 路由到明确的 Runtime capability。

    chat
    → Agent

    memory.*
    → Memory protocol handler
    """

    def __init__(
        self,
        *,
        chat_processor: MessageProcessor,
        memory_processor: MessageProcessor,
    ) -> None:
        self._chat_processor = chat_processor
        self._memory_processor = memory_processor

    async def process_message(
        self,
        message: Message,
    ) -> Message:
        if message.type == "chat":
            return await self._chat_processor.process_message(
                message
            )

        if message.type.startswith("memory."):
            return await self._memory_processor.process_message(
                message
            )

        return Message(
            type="error",
            source="agent_core",
            payload={
                "message": "Unsupported message type",
            },
        )
