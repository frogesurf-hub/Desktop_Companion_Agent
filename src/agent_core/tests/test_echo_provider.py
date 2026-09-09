import asyncio

from agent_core.providers import (
    LLMMessage,
    LLMRequest,
)
from agent_core.providers.echo import EchoLLMProvider


def test_echo_provider_preserves_phase_zero_response() -> None:
    """
    验证临时 Echo Provider 保持 Phase 0 的回声文本语义。
    """

    provider = EchoLLMProvider()

    request = LLMRequest(
        messages=(
            LLMMessage(
                role="user",
                content="你好",
            ),
        ),
    )

    response = asyncio.run(
        provider.generate(
            request,
        )
    )

    assert response.content == "收到你的消息: 你好"
