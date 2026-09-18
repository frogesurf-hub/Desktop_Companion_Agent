import asyncio
from pathlib import Path

import pytest
from pydantic import SecretStr

from agent_core import main as main_module
from agent_core.characters import (
    CharacterDefinition,
    CharacterNotFoundError,
)
from agent_core.composition import PromptContextComposer
from agent_core.config import Settings
from agent_core.providers import ProviderConfigurationError
from agent_core.temporal import (
    Clock,
    SystemClock,
)


def test_default_active_character_is_builtin_aria() -> None:
    """
    验证默认 Runtime Character 是随包分发的 Aria。
    """

    settings = _make_settings()

    character = main_module._load_active_character(
        settings,
    )

    assert character.character_id == "aria"
    assert character.display_name == "Aria"


def test_active_character_can_be_selected_from_configured_directory(
    tmp_path: Path,
) -> None:
    """
    验证外部 Character 目录和 active ID 可以由 Settings 指定。
    """

    character_path = (
        tmp_path
        / "custom.toml"
    )

    character_path.write_text(
        '''
character_id = "custom"
display_name = "Custom"

[identity]
description = """
A custom companion.
"""

[persona]
description = """
Calm.
"""

[speech_style]
description = """
Concise.
"""
'''.strip(),
        encoding="utf-8",
    )

    settings = _make_settings(
        character_definitions_dir=tmp_path,
        active_character_id="custom",
    )

    character = main_module._load_active_character(
        settings,
    )

    assert character.character_id == "custom"
    assert character.display_name == "Custom"


def test_unknown_active_character_id_is_rejected(
    tmp_path: Path,
) -> None:
    """
    验证配置的 active Character 不存在时启动边界显式失败。
    """

    character_path = (
        tmp_path
        / "available.toml"
    )

    character_path.write_text(
        '''
character_id = "available"
display_name = "Available"

[identity]
description = """
An available companion.
"""

[persona]
description = """
Calm.
"""

[speech_style]
description = """
Concise.
"""
'''.strip(),
        encoding="utf-8",
    )

    settings = _make_settings(
        character_definitions_dir=tmp_path,
        active_character_id="missing",
    )

    with pytest.raises(
        CharacterNotFoundError,
        match="missing",
    ):
        main_module._load_active_character(
            settings,
        )


def _make_settings(
    *,
    api_key: str | None = "test-secret-key",
    model_provider: str = "deepseek",
    character_definitions_dir: Path | None = None,
    active_character_id: str = "aria",
) -> Settings:
    """
    创建 Composition Root 测试使用的确定性 Settings。
    """

    secret = (
        SecretStr(
            api_key,
        )
        if api_key is not None
        else None
    )

    return Settings(
        app_name="Test Companion",
        environment="test",
        runtime_mode="cloud",
        websocket_host="127.0.0.1",
        websocket_port=9999,
        event_bus_queue_capacity=17,
        model_provider=model_provider,
        deepseek_api_key=secret,
        deepseek_model="deepseek-flash",
        deepseek_timeout_seconds=45.0,
        deepseek_thinking_enabled=False,
        log_level="DEBUG",
        character_definitions_dir=character_definitions_dir,
        active_character_id=active_character_id,
    )


def _install_runtime_fakes(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[tuple[str, object]],
    settings: Settings,
    *,
    server_error: Exception | None = None,
    event_bus_init_error: Exception | None = None,
    event_bus_start_error: Exception | None = None,
    event_bus_close_error: Exception | None = None,
    character_load_error: Exception | None = None,
) -> CharacterDefinition:
    """
    替换 Composition Root 外部组件，
    避免真实网络、SDK client 和后台 Event Bus task。
    """

    test_character = CharacterDefinition(
        character_id="test",
        display_name="Test",
        identity="A test companion.",
        persona="Calm.",
        speech_style="Concise.",
    )

    class FakeDeepSeekProvider:
        def __init__(
            self,
            api_key: str,
            model: str,
            timeout_seconds: float,
            thinking_enabled: bool,
        ) -> None:
            calls.append(
                (
                    "provider_init",
                    {
                        "api_key": api_key,
                        "model": model,
                        "timeout_seconds": timeout_seconds,
                        "thinking_enabled": thinking_enabled,
                    },
                )
            )

        async def aclose(self) -> None:
            calls.append(
                (
                    "provider_close",
                    None,
                )
            )

    class FakeEventBus:
        def __init__(
            self,
            *,
            queue_capacity: int,
        ) -> None:
            calls.append(
                (
                    "event_bus_init",
                    queue_capacity,
                )
            )

            if event_bus_init_error is not None:
                raise event_bus_init_error

        async def start(self) -> None:
            calls.append(
                (
                    "event_bus_start",
                    None,
                )
            )

            if event_bus_start_error is not None:
                raise event_bus_start_error

        async def close(self) -> None:
            calls.append(
                (
                    "event_bus_close",
                    None,
                )
            )

            if event_bus_close_error is not None:
                raise event_bus_close_error

    class FakeAgent:
        def __init__(
            self,
            provider: object,
            *,
            character: CharacterDefinition,
            composer: PromptContextComposer,
            clock: Clock,
            memory_retriever=None
        ) -> None:
            self.character = character
            self.composer = composer
            self.clock = clock
            self.memory_retriever = memory_retriever
            calls.append(
                (
                    "agent_init",
                    {
                        "provider": provider,
                        "character": character,
                        "composer": composer,
                        "clock": clock,
                    },
                )
            )

    class FakeWebSocketServer:
        def __init__(
            self,
            host: str,
            port: int,
            agent: object,
        ) -> None:
            calls.append(
                (
                    "server_init",
                    (
                        host,
                        port,
                        agent,
                    ),
                )
            )

        async def run(self) -> None:
            calls.append(
                (
                    "server_run",
                    None,
                )
            )

            if server_error is not None:
                raise server_error

    def fake_get_settings() -> Settings:
        calls.append(
            (
                "get_settings",
                None,
            )
        )

        return settings

    def fake_setup_logging(
        log_level: str,
    ) -> None:
        calls.append(
            (
                "setup_logging",
                log_level,
            )
        )



    monkeypatch.setattr(
        main_module,
        "get_settings",
        fake_get_settings,
    )

    def fake_load_active_character(
        _settings: Settings,
    ) -> CharacterDefinition:
        if character_load_error is not None:
            raise character_load_error

        return test_character

    monkeypatch.setattr(
        main_module,
        "_load_active_character",
        fake_load_active_character,
    )

    monkeypatch.setattr(
        main_module,
        "setup_logging",
        fake_setup_logging,
    )

    monkeypatch.setattr(
        main_module,
        "DeepSeekProvider",
        FakeDeepSeekProvider,
    )

    monkeypatch.setattr(
        main_module,
        "EventBus",
        FakeEventBus,
    )

    monkeypatch.setattr(
        main_module,
        "Agent",
        FakeAgent,
    )

    monkeypatch.setattr(
        main_module,
        "WebSocketServer",
        FakeWebSocketServer,
    )
    return test_character


def test_provider_is_not_created_when_character_loading_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[
        tuple[str, object]
    ] = []

    settings = _make_settings()

    _install_runtime_fakes(
        monkeypatch,
        calls,
        settings,
        character_load_error=RuntimeError(
            "character load failed",
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="character load failed",
    ):
        asyncio.run(
            main_module.run(),
        )

    assert not any(
        name == "provider_init"
        for name, _ in calls
    )

    assert not any(
        name == "event_bus_init"
        for name, _ in calls
    )


def test_provider_is_closed_when_event_bus_construction_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    验证 Event Bus 构造失败时，
    已创建的 Provider 仍然会被关闭。
    """

    calls: list[
        tuple[str, object]
    ] = []

    settings = _make_settings()

    _install_runtime_fakes(
        monkeypatch,
        calls,
        settings,
        event_bus_init_error=RuntimeError(
            "event bus init failed",
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="event bus init failed",
    ):
        asyncio.run(
            main_module.run(),
        )

    assert (
        "event_bus_init",
        17,
    ) in calls

    assert not any(
        name == "agent_init"
        for name, _ in calls
    )

    assert not any(
        name == "event_bus_start"
        for name, _ in calls
    )

    assert not any(
        name == "event_bus_close"
        for name, _ in calls
    )

    assert calls[-1] == (
        "provider_close",
        None,
    )


def test_run_initializes_deepseek_and_event_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    验证 Composition Root：

    1. 读取 Settings
    2. 初始化 Logging
    3. 创建 DeepSeek Provider
    4. 创建 Event Bus
    5. 注入 Agent
    6. 创建 WebSocketServer
    7. 启动 Event Bus
    8. 启动 Server
    9. 关闭 Event Bus
    10. 关闭 Provider
    """

    calls: list[
        tuple[str, object]
    ] = []

    settings = _make_settings()

    test_character = _install_runtime_fakes(
        monkeypatch,
        calls,
        settings,
    )

    asyncio.run(
        main_module.run(),
    )

    assert calls[0] == (
        "get_settings",
        None,
    )

    assert calls[1] == (
        "setup_logging",
        "DEBUG",
    )

    assert calls[2] == (
        "provider_init",
        {
            "api_key": "test-secret-key",
            "model": "deepseek-flash",
            "timeout_seconds": 45.0,
            "thinking_enabled": False,
        },
    )

    assert calls[3] == (
        "event_bus_init",
        17,
    )

    assert calls[4][0] == "agent_init"

    agent_init = calls[4][1]

    assert isinstance(
        agent_init,
        dict,
    )

    assert agent_init["character"] is test_character
    assert isinstance(
        agent_init["composer"],
        PromptContextComposer,
    )

    assert isinstance(
        agent_init["clock"],
        SystemClock,
    )

    assert calls[5][0] == "server_init"

    assert calls[6] == (
        "event_bus_start",
        None,
    )

    assert calls[7] == (
        "server_run",
        None,
    )

    assert calls[8] == (
        "event_bus_close",
        None,
    )

    assert calls[9] == (
        "provider_close",
        None,
    )


def test_missing_deepseek_api_key_is_rejected() -> None:
    """
    验证缺少 DeepSeek API Key 时启动立即失败。
    """

    settings = _make_settings(
        api_key=None,
    )

    with pytest.raises(
        ProviderConfigurationError,
    ):
        main_module._create_provider(
            settings,
        )


def test_unsupported_model_provider_is_rejected() -> None:
    """
    验证 Phase 1 尚未支持的 Provider
    不会被静默替换或忽略。
    """

    settings = _make_settings(
        model_provider="unsupported",
    )

    with pytest.raises(
        ProviderConfigurationError,
    ):
        main_module._create_provider(
            settings,
        )


def test_runtime_resources_are_closed_when_server_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    验证 WebSocketServer 异常退出时，
    Event Bus 与 Provider 都会被关闭。
    """

    calls: list[
        tuple[str, object]
    ] = []

    settings = _make_settings()

    _install_runtime_fakes(
        monkeypatch,
        calls,
        settings,
        server_error=RuntimeError(
            "server failed",
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="server failed",
    ):
        asyncio.run(
            main_module.run(),
        )

    assert (
        "server_run",
        None,
    ) in calls

    assert calls[-2:] == [
        (
            "event_bus_close",
            None,
        ),
        (
            "provider_close",
            None,
        ),
    ]


def test_provider_is_closed_when_event_bus_start_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    验证 Event Bus 启动失败时，
    runtime cleanup 仍会关闭 Event Bus 和 Provider。
    """

    calls: list[
        tuple[str, object]
    ] = []

    settings = _make_settings()

    _install_runtime_fakes(
        monkeypatch,
        calls,
        settings,
        event_bus_start_error=RuntimeError(
            "event bus start failed",
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="event bus start failed",
    ):
        asyncio.run(
            main_module.run(),
        )

    assert (
        "server_run",
        None,
    ) not in calls

    assert calls[-2:] == [
        (
            "event_bus_close",
            None,
        ),
        (
            "provider_close",
            None,
        ),
    ]


def test_provider_is_closed_when_event_bus_close_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    验证 Event Bus cleanup 自身失败时，
    Provider cleanup 仍然执行。
    """

    calls: list[
        tuple[str, object]
    ] = []

    settings = _make_settings()

    _install_runtime_fakes(
        monkeypatch,
        calls,
        settings,
        event_bus_close_error=RuntimeError(
            "event bus close failed",
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="event bus close failed",
    ):
        asyncio.run(
            main_module.run(),
        )

    assert (
        "event_bus_close",
        None,
    ) in calls

    assert calls[-1] == (
        "provider_close",
        None,
    )
