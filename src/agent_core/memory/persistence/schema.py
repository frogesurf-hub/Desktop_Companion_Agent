from pathlib import Path

from alembic import command
from alembic.config import Config

_REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[4]
)
_ALEMBIC_CONFIG_PATH = (
    _REPOSITORY_ROOT
    / "alembic.ini"
)

_MIGRATIONS_PATH = (
    _REPOSITORY_ROOT
    / "migrations"
)


def upgrade_memory_database(
    database_path: Path,
) -> None:
    """
    将 Runtime Memory SQLite schema
    升级到当前 Alembic head。

    必须在 Repository 开始访问数据库之前执行。
    """

    resolved_path = (
        database_path
        .expanduser()
        .resolve()
    )

    resolved_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    config = Config(
        str(_ALEMBIC_CONFIG_PATH)
    )

    config.attributes[
        "configure_logger"
    ] = False

    config.set_main_option(
        "script_location",
        _MIGRATIONS_PATH.as_posix(),
    )

    config.set_main_option(
        "sqlalchemy.url",
        (
            "sqlite:///"
            f"{resolved_path.as_posix()}"
        ),
    )

    command.upgrade(
        config,
        "head",
    )
