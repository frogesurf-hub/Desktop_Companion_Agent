from agent_core.providers import LLMRequest, LLMResponse


class EchoLLMProvider:
    """
    Phase 0 回声行为的临时兼容 Provider。

    仅用于在真实云 Provider 接入前保持运行链路可执行。
    """

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        使用最后一条消息生成 Phase 0 兼容回声响应。
        """

        content = ""

        if request.messages:
            content = request.messages[-1].content

        return LLMResponse(
            content=f"收到你的消息: {content}",
        )
