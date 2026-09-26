import logging

from agent_core.characters import CharacterDefinition
from agent_core.composition import PromptContextComposer
from agent_core.core.message import Message
from agent_core.memory.learning import (
    MemoryLearningInput,
    MemoryTurnLearner,
)
from agent_core.memory.retriever import MemoryRetriever
from agent_core.providers import (
    LLMProvider,
    LLMProviderError,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderConnectionError,
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from agent_core.temporal import (
    Clock,
    TemporalContext,
)

logger = logging.getLogger(__name__)

_PROVIDER_ERROR_PROTOCOL_MAP: tuple[
    tuple[
        type[LLMProviderError],
        str,
        str,
    ],
    ...,
] = (
    (
        ProviderConfigurationError,
        "PROVIDER_NOT_CONFIGURED",
        "AI provider is not configured.",
    ),
    (
        ProviderAuthenticationError,
        "PROVIDER_AUTHENTICATION_FAILED",
        "AI provider authentication failed.",
    ),
    (
        ProviderQuotaError,
        "PROVIDER_QUOTA_EXHAUSTED",
        "AI provider quota or balance is insufficient.",
    ),
    (
        ProviderRateLimitError,
        "PROVIDER_RATE_LIMITED",
        "AI provider is rate-limited. Please try again later.",
    ),
    (
        ProviderTimeoutError,
        "PROVIDER_TIMEOUT",
        "AI provider request timed out.",
    ),
    (
        ProviderConnectionError,
        "PROVIDER_UNAVAILABLE",
        "AI provider is temporarily unavailable.",
    ),
    (
        ProviderUnavailableError,
        "PROVIDER_UNAVAILABLE",
        "AI provider is temporarily unavailable.",
    ),
    (
        ProviderRequestError,
        "PROVIDER_REQUEST_FAILED",
        "AI provider rejected the request.",
    ),
    (
        ProviderResponseError,
        "PROVIDER_INVALID_RESPONSE",
        "AI provider returned an invalid response.",
    ),
)


class Agent:
    """
    Agent 核心逻辑。

    当前负责：
    - 接收 chat 协议 Message
    - 读取注入的 Character / Clock / MemoryRetriever 上下文
    - 通过 PromptContextComposer 生成 Provider-neutral LLM 请求
    - 调用注入的 LLM Provider
    - 在 Provider 成功响应后可选执行 MemoryTurnLearner
    - 将 Provider 响应转换回协议 Message
    - 将 Provider 错误转换为安全的协议 error Message

    当前不负责：
    - Memory 持久化实现
    - Memory Governance
    - Situation / Attention / Behavior
    - Permission / Tool 执行
    """

    def __init__(
        self,
        provider: LLMProvider,
        name: str = "Desktop Companion",
        *,
        character: CharacterDefinition,
        composer: PromptContextComposer,
        clock: Clock,
        memory_retriever: MemoryRetriever,
        memory_learner: MemoryTurnLearner | None = None,
    ) -> None:
        self.name = name
        self._provider = provider
        self._character = character
        self._composer = composer
        self._memory_retriever = memory_retriever
        self._memory_learner = memory_learner
        self._clock = clock

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

            current_datetime = self._clock.now()

            temporal_context = TemporalContext(
                current_datetime=current_datetime,
            )

            memory_context = await self._memory_retriever.retrieve(
                user_text,
                character_id=self._character.character_id,
            )

            request = self._composer.compose(
                character=self._character,
                temporal_context=temporal_context,
                memory_context=memory_context,
                user_message=user_text,
            )

            try:
                provider_response = await self._provider.generate(
                    request,
                )

            except LLMProviderError as exc:
                logger.warning(
                    "LLM provider request failed: %s",
                    type(exc).__name__,
                )

                code, safe_message = self._map_provider_error(
                    exc,
                )

                return Message(
                    type="error",
                    source=self.name,
                    payload={
                        "code": code,
                        "message": safe_message,
                    },
                )

            if (
                self._memory_learner is not None
                and user_text.strip()
            ):
                learning_input = MemoryLearningInput(
                    source_message_id=message.id,
                    user_text=user_text,
                    assistant_text=(
                        provider_response.content
                    ),
                    active_character_id=(
                        self._character.character_id
                    ),
                    occurred_at=current_datetime,
                )

                await self._memory_learner.learn_turn(
                    learning_input
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

    @staticmethod
    def _map_provider_error(
        error: LLMProviderError,
    ) -> tuple[str, str]:
        """
        将 Provider-neutral error
        转换为稳定的 Desktop protocol code/message。
        """

        for (
            error_type,
            code,
            safe_message,
        ) in _PROVIDER_ERROR_PROTOCOL_MAP:
            if isinstance(
                error,
                error_type,
            ):
                return (
                    code,
                    safe_message,
                )

        return (
            "PROVIDER_ERROR",
            "AI provider request failed.",
        )
