from datetime import (
    datetime,
    timedelta,
    timezone,
)

from agent_core.characters import CharacterDefinition
from agent_core.composition import PromptContextComposer
from agent_core.core.agent import Agent
from agent_core.memory.retrieval import PreparedMemoryContext
from agent_core.providers import (
    LLMProvider,
    LLMProviderError,
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


class FailingLLMProvider:
    """
    测试专用的确定性失败 Provider。

    用于验证 Agent 和协议错误边界。
    """

    def __init__(
        self,
        error: LLMProviderError,
    ) -> None:
        self._error = error
        self.requests: list[LLMRequest] = []

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        记录请求并抛出预设 Provider error。
        """

        self.requests.append(
            request,
        )

        raise self._error


class FixedClock:
    """
    测试使用的确定性 Clock。
    """

    def __init__(
        self,
        current_datetime: datetime,
    ) -> None:
        self._current_datetime = current_datetime

    def now(self) -> datetime:
        return self._current_datetime


class FakeMemoryRetriever:
    """
    Test-only Memory Retriever.

    Does not access repository/database.
    Returns predefined PreparedMemoryContext.
    """

    def __init__(
        self,
        context: PreparedMemoryContext,
    ) -> None:
        self._context = context
        self.queries: list[str] = []

    async def retrieve(
        self,
        query: str,
    ) -> PreparedMemoryContext:
        self.queries.append(
            query,
        )

        return self._context


def create_test_agent(
    provider: LLMProvider,
    *,
    memory_context: PreparedMemoryContext | None = None,
) -> Agent:
    """
    创建具备完整 Phase 3 Runtime dependencies 的测试 Agent。
    """
    if memory_context is None:
        memory_context = PreparedMemoryContext()

    memory_retriever = FakeMemoryRetriever(
        memory_context,
    )

    return Agent(
        provider=provider,
        character=CharacterDefinition(
            character_id="test",
            display_name="Test",
            identity="A test companion.",
            persona="Calm.",
            speech_style="Concise.",
        ),
        composer=PromptContextComposer(),
        clock=FixedClock(
            datetime(
                2026,
                9,
                13,
                20,
                0,
                tzinfo=timezone(
                    timedelta(hours=8),
                ),
            )
        ),
        memory_retriever=memory_retriever,
    )
