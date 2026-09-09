from pathlib import Path

import pytest
from pydantic import ValidationError

from agent_core.config import Settings

DCA_ENVIRONMENT_VARIABLES = [
    "DCA_APP_NAME",
    "DCA_ENVIRONMENT",
    "DCA_RUNTIME_MODE",
    "DCA_WEBSOCKET_HOST",
    "DCA_WEBSOCKET_PORT",
    "DCA_MODEL_PROVIDER",
    "DCA_DEEPSEEK_API_KEY",
    "DCA_DEEPSEEK_MODEL",
    "DCA_DEEPSEEK_TIMEOUT_SECONDS",
    "DCA_DEEPSEEK_THINKING_ENABLED",
    "DCA_LOG_LEVEL",
]


def clear_dca_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    清除可能影响测试的 Desktop Companion Agent 环境变量。
    """

    for variable in DCA_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(
            variable,
            raising=False,
        )


def test_settings_default_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    验证没有外部配置时，
    Settings 使用预期默认值。
    """

    clear_dca_environment(
        monkeypatch,
    )

    monkeypatch.chdir(
        tmp_path,
    )

    settings = Settings()

    assert settings.app_name == "Desktop Companion Agent"

    assert settings.environment == "development"

    assert settings.runtime_mode == "hybrid"

    assert settings.websocket_host == "127.0.0.1"
    assert settings.websocket_port == 8765

    assert settings.model_provider == "deepseek"

    assert settings.deepseek_api_key is None

    assert settings.deepseek_model == "deepseek-v4-flash"

    assert settings.deepseek_timeout_seconds == 60.0

    assert settings.deepseek_thinking_enabled is False

    assert settings.log_level == "INFO"


def test_environment_variables_override_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    验证 DCA_ 环境变量能够覆盖 Settings 默认值。
    """

    clear_dca_environment(
        monkeypatch,
    )

    monkeypatch.chdir(
        tmp_path,
    )

    monkeypatch.setenv(
        "DCA_RUNTIME_MODE",
        "local",
    )

    monkeypatch.setenv(
        "DCA_WEBSOCKET_PORT",
        "9001",
    )

    monkeypatch.setenv(
        "DCA_DEEPSEEK_MODEL",
        "deepseek-v4-pro",
    )

    monkeypatch.setenv(
        "DCA_DEEPSEEK_TIMEOUT_SECONDS",
        "45",
    )

    monkeypatch.setenv(
        "DCA_DEEPSEEK_THINKING_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "DCA_LOG_LEVEL",
        "DEBUG",
    )

    settings = Settings()

    assert settings.runtime_mode == "local"

    assert settings.websocket_port == 9001

    assert settings.deepseek_model == "deepseek-v4-pro"

    assert settings.deepseek_timeout_seconds == 45.0

    assert settings.deepseek_thinking_enabled is True

    assert settings.log_level == "DEBUG"


def test_invalid_runtime_mode_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    验证非法 runtime_mode 会触发配置校验错误。
    """

    clear_dca_environment(
        monkeypatch,
    )

    monkeypatch.chdir(
        tmp_path,
    )

    monkeypatch.setenv(
        "DCA_RUNTIME_MODE",
        "invalid-mode",
    )

    with pytest.raises(
        ValidationError,
    ):
        Settings()


def test_invalid_deepseek_timeout_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    验证 DeepSeek timeout 必须大于零。
    """

    clear_dca_environment(
        monkeypatch,
    )

    monkeypatch.chdir(
        tmp_path,
    )

    monkeypatch.setenv(
        "DCA_DEEPSEEK_TIMEOUT_SECONDS",
        "0",
    )

    with pytest.raises(
        ValidationError,
    ):
        Settings()


def test_deepseek_api_key_is_stored_as_secret(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    验证 DeepSeek API Key 使用 SecretStr 保存。
    """

    clear_dca_environment(
        monkeypatch,
    )

    monkeypatch.chdir(
        tmp_path,
    )

    api_key = "test-secret-key"

    monkeypatch.setenv(
        "DCA_DEEPSEEK_API_KEY",
        api_key,
    )

    settings = Settings()

    assert settings.deepseek_api_key is not None

    assert (
        settings.deepseek_api_key.get_secret_value()
        == api_key
    )

    assert str(
        settings.deepseek_api_key,
    ) != api_key
