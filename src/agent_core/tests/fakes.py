from agent_core.providers import (
    LLMRequest,
    LLMResponse,
)


class FakeLLMProvider:
    """
    测试专用的确定性 LLM Provider。

    不访问网络，也不需要真实 API Key。
    """

    def __init__(
        self,
        response: LLMResponse,
    ) -> None:
        self._response = response
        self.requests: list[LLMRequest] = []

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        记录请求并返回预设响应。
        """

        self.requests.append(
            request,
        )

        return self._response
