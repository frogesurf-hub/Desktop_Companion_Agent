from agent_core.core.message import Message
from agent_core.providers import (
    LLMMessage,
    LLMProvider,
    LLMRequest,
)


class Agent:
    """
    Agent 核心逻辑。

    当前阶段负责：
    - 接收协议 Message
    - 转换为 Provider-neutral LLM 请求
    - 调用注入的 LLM Provider
    - 将 Provider 响应转换回协议 Message

    后续会继续接入：
    - Memory
    - Behavior
    - Tool
    """

    def __init__(
        self,
        provider: LLMProvider,
        name: str = "Desktop Companion",
    ) -> None:
        self.name = name
        self._provider = provider

    async def process_message(
        self,
        message: Message,
    ) -> Message:
        """
        异步处理输入消息并返回统一 Message。
        """

        if message.type == "chat":
            user_text = message.payload.get(
                "message",
                "",
            )

            request = LLMRequest(
                messages=(
                    LLMMessage(
                        role="user",
                        content=user_text,
                    ),
                ),
            )

            provider_response = await self._provider.generate(
                request,
            )

            return Message(
                type="response",
                source=self.name,
                payload={
                    "message": provider_response.content,
                },
            )

        return Message(
            type="error",
            source=self.name,
            payload={
                "message": "Unsupported message type",
            },
        )
