import asyncio
import logging

from agent_core.communication import WebSocketServer
from agent_core.config import get_settings
from agent_core.core.agent import Agent
from agent_core.observability import setup_logging
from agent_core.providers.echo import EchoLLMProvider

logger = logging.getLogger(__name__)


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

    logger.warning(
        "Real LLM provider adapter is not wired yet; "
        "using the Phase 0 echo compatibility provider",
    )

    logger.info(
        "WebSocket endpoint: %s:%s",
        settings.websocket_host,
        settings.websocket_port,
    )

    provider = EchoLLMProvider()

    agent = Agent(
        provider=provider,
    )

    server = WebSocketServer(
        host=settings.websocket_host,
        port=settings.websocket_port,
        agent=agent,
    )

    await server.run()


def main() -> None:
    """
    Desktop Companion Agent Core 的同步程序入口。
    """

    asyncio.run(
        run(),
    )


if __name__ == "__main__":
    main()
