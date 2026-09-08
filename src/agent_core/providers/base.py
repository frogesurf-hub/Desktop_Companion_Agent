from typing import Protocol

from agent_core.providers.models import (
    LLMRequest,
    LLMResponse,
)


class LLMProvider(Protocol):
    """
    LLM Provider 的统一异步契约。

    Agent Core 只依赖该接口，
    不依赖任何具体模型厂商实现。
    """

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        根据 Provider-neutral 请求生成完整响应。
        """

        ...
