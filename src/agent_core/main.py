import asyncio
import logging

from agent_core.communication import WebSocketServer
from agent_core.config import Settings, get_settings
from agent_core.core.agent import Agent
from agent_core.events import EventBus
from agent_core.observability import setup_logging
from agent_core.providers import ProviderConfigurationError
from agent_core.providers.deepseek import DeepSeekProvider

logger = logging.getLogger(__name__)


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


async def run() -> None:
    """
    初始化并运行 Desktop Companion Agent Core。
    """

    settings = get_settings()

    setup_logging(
        log_level=settings.log_level,
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

    provider = _create_provider(
        settings,
    )

    try:
        event_bus = EventBus(
            queue_capacity=settings.event_bus_queue_capacity,
        )

        try:
            agent = Agent(
                provider=provider,
            )

            server = WebSocketServer(
                host=settings.websocket_host,
                port=settings.websocket_port,
                agent=agent,
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
