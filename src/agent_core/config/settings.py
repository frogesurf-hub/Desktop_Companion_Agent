from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Desktop Companion Agent 的统一运行配置。

    配置主要来自：
    1. 默认值
    2. .env 文件
    3. 系统环境变量

    后续所有模块都应通过 Settings 获取配置，
    而不是在各自文件中硬编码。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DCA_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Desktop Companion Agent"

    environment: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    runtime_mode: Literal[
        "offline",
        "local",
        "hybrid",
        "cloud",
    ] = "hybrid"

    websocket_host: str = "127.0.0.1"
    websocket_port: int = 8765

    model_provider: str = "deepseek"

    deepseek_api_key: SecretStr | None = None

    deepseek_model: str = "deepseek-v4-flash"

    deepseek_timeout_seconds: float = Field(
        default=60.0,
        gt=0,
    )

    deepseek_thinking_enabled: bool = False

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    返回当前进程共享的 Settings 实例。

    使用缓存可以避免程序不同模块反复读取和解析配置。
    """

    return Settings()
