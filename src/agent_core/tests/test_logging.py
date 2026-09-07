import logging
from pathlib import Path

from agent_core.observability.logging import DEFAULT_LOG_FILE, setup_logging


def test_setup_logging_creates_log_file(tmp_path: Path) -> None:
    """
    验证初始化日志系统后会创建日志文件。
    """

    setup_logging(
        log_level="INFO",
        log_directory=tmp_path,
    )

    log_file = tmp_path / DEFAULT_LOG_FILE

    assert log_file.exists()


def test_log_message_is_written_to_file(tmp_path: Path) -> None:
    """
    验证日志内容能够写入日志文件。
    """

    setup_logging(
        log_level="INFO",
        log_directory=tmp_path,
    )

    logger = logging.getLogger("agent_core.test")

    message = "logging test message"
    logger.info(message)

    for handler in logging.getLogger().handlers:
        handler.flush()

    log_file = tmp_path / DEFAULT_LOG_FILE
    content = log_file.read_text(encoding="utf-8")

    assert message in content


def test_log_level_filters_debug_messages(tmp_path: Path) -> None:
    """
    验证 INFO 日志等级会过滤 DEBUG 日志。
    """

    setup_logging(
        log_level="INFO",
        log_directory=tmp_path,
    )

    logger = logging.getLogger("agent_core.test")

    debug_message = "debug message should not appear"
    info_message = "info message should appear"

    logger.debug(debug_message)
    logger.info(info_message)

    for handler in logging.getLogger().handlers:
        handler.flush()

    log_file = tmp_path / DEFAULT_LOG_FILE
    content = log_file.read_text(encoding="utf-8")

    assert debug_message not in content
    assert info_message in content


def test_setup_logging_does_not_duplicate_handlers(tmp_path: Path) -> None:
    """
    验证重复初始化日志系统不会不断叠加 Handler。
    """

    setup_logging(
        log_level="INFO",
        log_directory=tmp_path,
    )

    first_handler_count = len(
        logging.getLogger().handlers,
    )

    setup_logging(
        log_level="INFO",
        log_directory=tmp_path,
    )

    second_handler_count = len(
        logging.getLogger().handlers,
    )

    assert first_handler_count == 2
    assert second_handler_count == 2
