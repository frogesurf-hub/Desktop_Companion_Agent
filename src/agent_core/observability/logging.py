import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

DEFAULT_LOG_DIRECTORY = Path("logs")
DEFAULT_LOG_FILE = "agent_core.log"

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    log_level: str = "INFO",
    log_directory: Path | None = None,
) -> None:
    """
    配置 Desktop Companion Agent 的全局日志系统。

    日志同时输出到：
    1. 控制台
    2. 本地滚动日志文件

    此函数应在 Agent Core 启动时调用一次。
    """

    if log_directory is None:
        log_directory = DEFAULT_LOG_DIRECTORY

    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    root_logger = logging.getLogger()

    root_logger.setLevel(
        log_level.upper(),
    )

    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=log_directory / DEFAULT_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
