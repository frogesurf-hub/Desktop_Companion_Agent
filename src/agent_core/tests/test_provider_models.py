from dataclasses import FrozenInstanceError

import pytest

from agent_core.providers import (
    LLMMessage,
    LLMRequest,
    LLMResponse,
)


def test_llm_request_preserves_messages() -> None:
    """
    验证 Provider-neutral 请求可以保存消息序列。
    """

    message = LLMMessage(
        role="user",
        content="你好",
    )

    request = LLMRequest(
        messages=(
            message,
        ),
    )

    assert request.messages == (
        message,
    )

    assert request.messages[0].role == "user"
    assert request.messages[0].content == "你好"


def test_llm_response_preserves_content() -> None:
    """
    验证 Provider-neutral 响应可以保存文本内容。
    """

    response = LLMResponse(
        content="你好，有什么可以帮你的？",
    )

    assert (
        response.content
        == "你好，有什么可以帮你的？"
    )


def test_provider_models_are_immutable() -> None:
    """
    验证 Provider 边界数据对象不可原地修改。
    """

    message = LLMMessage(
        role="user",
        content="original",
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        setattr(
            message,
            "content",
            "changed",
        )
