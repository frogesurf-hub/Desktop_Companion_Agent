from dataclasses import dataclass
from typing import Literal

LLMRole = Literal[
    "system",
    "user",
    "assistant",
]


@dataclass(
    frozen=True,
    slots=True,
)
class LLMMessage:
    """
    Provider-neutral LLM 消息。
    """

    role: LLMRole
    content: str


@dataclass(
    frozen=True,
    slots=True,
)
class LLMRequest:
    """
    Provider-neutral LLM 请求。
    """

    messages: tuple[LLMMessage, ...]


@dataclass(
    frozen=True,
    slots=True,
)
class LLMResponse:
    """
    Provider-neutral LLM 响应。
    """

    content: str
