import asyncio
import logging
from pathlib import Path

from agent_core.characters import (
    CharacterDefinition,
    load_character_definitions,
    resolve_character,
)
from agent_core.communication import WebSocketServer
from agent_core.composition import PromptContextComposer
from agent_core.config import Settings, get_settings
from agent_core.core.agent import Agent
from agent_core.core.message_router import (
    RuntimeMessageRouter,
)
from agent_core.events import EventBus
from agent_core.memory import (
    HealthAwareMemoryGovernanceService,
    MemoryGovernanceService,
    MemoryHealthTracker,
    MemoryRetrievalLimits,
    MemoryRetrievalPolicy,
    MemoryRetrievalService,
    ResilientMemoryRetriever,
)
from agent_core.memory.conflict import (
    MemoryConflictPolicy,
)
from agent_core.memory.learning import (
    AutomaticMemoryTurnLearner,
    ExistingMemoryResolver,
    LLMMemoryCandidateExtractor,
    MemoryLearningPolicy,
    MemoryLearningService,
    ResilientMemoryTurnLearner,
)
from agent_core.memory.persistence import (
    SQLiteMemoryRepository,
    create_memory_engine,
    create_memory_session_factory,
    upgrade_memory_database,
)
from agent_core.memory.protocol import (
    MemoryProtocolHandler,
)
from agent_core.observability import setup_logging
from agent_core.providers import ProviderConfigurationError
from agent_core.providers.deepseek import DeepSeekProvider
from agent_core.temporal import SystemClock

logger = logging.getLogger(__name__)


_BUILTIN_CHARACTER_DEFINITIONS_DIR = (
    Path(__file__).resolve().parent
    / "characters"
    / "definitions"
)


def _load_active_character(
    settings: Settings,
) -> CharacterDefinition:
    """
    根据 Runtime Settings 加载并解析当前活动 Character。

    未配置外部 Character 目录时，
    使用随 agent_core package 分发的内置 definitions。
    """

    definitions_dir = (
        settings.character_definitions_dir
        if settings.character_definitions_dir is not None
        else _BUILTIN_CHARACTER_DEFINITIONS_DIR
    )

    definitions = load_character_definitions(
        definitions_dir,
    )

    return resolve_character(
        definitions,
        settings.active_character_id,
    )


def _create_provider(
    settings: Settings,
) -> DeepSeekProvider:
    """
    根据当前配置创建 Phase 1 支持的具体 LLM Provider。

    SecretStr 只允许在这个 Composition Root 边界解包。
    """

    if settings.model_provider != "deepseek":
        raise ProviderConfigurationError(
            "Unsupported model provider configuration",
        )

    if settings.deepseek_api_key is None:
        raise ProviderConfigurationError(
            "DeepSeek API key is missing",
        )

    return DeepSeekProvider(
        api_key=settings.deepseek_api_key.get_secret_value(),
        model=settings.deepseek_model,
        timeout_seconds=settings.deepseek_timeout_seconds,
        thinking_enabled=settings.deepseek_thinking_enabled,
    )


def _create_memory_learner(
    *,
    settings: Settings,
    provider: DeepSeekProvider,
    clock: SystemClock,
    repository: SQLiteMemoryRepository,
    health: MemoryHealthTracker,
) -> ResilientMemoryTurnLearner | None:
    """
    根据 Runtime Settings 组装 Automatic Memory Learning。

    Composition Root 负责把具体组件连接起来，
    Agent 仍只依赖 MemoryTurnLearner 边界。
    """

    if not settings.automatic_learning_enabled:
        return None

    extractor = LLMMemoryCandidateExtractor(
        provider=provider,
        clock=clock,
    )

    resolver = ExistingMemoryResolver(
        repository=repository,
    )

    learning_service = MemoryLearningService(
        repository=repository,
        policy=MemoryLearningPolicy(),
        resolver=resolver,
        conflict_policy=MemoryConflictPolicy(),
    )

    automatic_learner = AutomaticMemoryTurnLearner(
        extractor=extractor,
        learning_service=learning_service,
    )

    return ResilientMemoryTurnLearner(
        learner=automatic_learner,
        health=health,
    )


async def run() -> None:
    """
    初始化并运行 Desktop Companion Agent Core。
    """

    settings = get_settings()

    setup_logging(
        log_level=settings.log_level,
    )

    active_character = _load_active_character(
        settings,
    )

    composer = PromptContextComposer()
    clock = SystemClock()

    upgrade_memory_database(
        settings.memory_database_path,
    )

    memory_engine = create_memory_engine(
        settings.memory_database_path,
    )

    memory_session_factory = create_memory_session_factory(
        memory_engine,
    )

    memory_repository = SQLiteMemoryRepository(
        session_factory=memory_session_factory,
    )

    memory_health = MemoryHealthTracker()

    memory_policy = MemoryRetrievalPolicy(
        limits=MemoryRetrievalLimits(),
    )

    memory_retrieval_service = MemoryRetrievalService(
        repository=memory_repository,
        policy=memory_policy,
    )

    memory_retriever = ResilientMemoryRetriever(
        retriever=memory_retrieval_service,
        health=memory_health,
    )

    provider = _create_provider(
        settings,
    )



    logger.info(
        "Starting %s",
        settings.app_name,
    )

    logger.info(
        "Environment: %s",
        settings.environment,
    )

    logger.info(
        "Runtime mode: %s",
        settings.runtime_mode,
    )

    logger.info(
        "Configured model provider: %s",
        settings.model_provider,
    )

    logger.info(
        "Configured DeepSeek model: %s",
        settings.deepseek_model,
    )

    logger.info(
        "WebSocket endpoint: %s:%s",
        settings.websocket_host,
        settings.websocket_port,
    )

    try:
        memory_learner = _create_memory_learner(
            settings=settings,
            provider=provider,
            clock=clock,
            repository=memory_repository,
            health=memory_health,
        )

        event_bus = EventBus(
            queue_capacity=settings.event_bus_queue_capacity,
        )

        try:
            agent = Agent(
                provider=provider,
                character=active_character,
                composer=composer,
                clock=clock,
                memory_retriever=memory_retriever,
                memory_learner=memory_learner,
            )

            memory_governance_service = MemoryGovernanceService(
                repository=memory_repository,
                clock=clock,
            )

            memory_governance = (
                HealthAwareMemoryGovernanceService(
                    governance=memory_governance_service,
                    health=memory_health,
                )
            )

            memory_protocol = MemoryProtocolHandler(
                governance=memory_governance,
            )

            runtime_router = RuntimeMessageRouter(
                chat_processor=agent,
                memory_processor=memory_protocol,
            )

            server = WebSocketServer(
                host=settings.websocket_host,
                port=settings.websocket_port,
                processor=runtime_router,
            )

            await event_bus.start()

            await server.run()

        finally:
            await event_bus.close()

    finally:
        await provider.aclose()


def main() -> None:
    """
    Desktop Companion Agent Core 的同步程序入口。
    """

    asyncio.run(
        run(),
    )


if __name__ == "__main__":
    main()
