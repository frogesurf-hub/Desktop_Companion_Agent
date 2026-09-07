import logging

from agent_core.config import get_settings
from agent_core.observability import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Desktop Companion Agent Core 的应用入口。

    负责初始化运行时基础设施，并启动 Agent Core。
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
        "Model provider: %s",
        settings.model_provider,
    )

    logger.info(
        "WebSocket endpoint: %s:%s",
        settings.websocket_host,
        settings.websocket_port,
    )


if __name__ == "__main__":
    main()
