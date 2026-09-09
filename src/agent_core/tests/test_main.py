import asyncio

from agent_core import main as main_module


def test_run_initializes_runtime(
    monkeypatch,
) -> None:
    """
    验证 run() 会：

    1. 读取 Settings
    2. 初始化 Logging
    3. 创建兼容 Provider
    4. 将 Provider 注入 Agent
    5. 创建 WebSocketServer
    6. 启动 WebSocketServer
    """

    calls: list[tuple[str, object]] = []

    class FakeSettings:
        app_name = "Test Companion"
        environment = "test"
        runtime_mode = "offline"
        model_provider = "test-provider"
        websocket_host = "127.0.0.1"
        websocket_port = 9999
        log_level = "DEBUG"

    class FakeEchoLLMProvider:
        def __init__(self) -> None:
            calls.append(
                ("provider_init", None),
            )

    class FakeAgent:
        def __init__(
            self,
            provider: FakeEchoLLMProvider,
        ) -> None:
            calls.append(
                ("agent_init", provider),
            )

    class FakeWebSocketServer:
        def __init__(
            self,
            host: str,
            port: int,
            agent: FakeAgent,
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
                ("server_run", None),
            )

    def fake_get_settings() -> FakeSettings:
        calls.append(
            ("get_settings", None),
        )
        return FakeSettings()

    def fake_setup_logging(
        log_level: str,
    ) -> None:
        calls.append(
            ("setup_logging", log_level),
        )

    monkeypatch.setattr(
        main_module,
        "get_settings",
        fake_get_settings,
    )

    monkeypatch.setattr(
        main_module,
        "setup_logging",
        fake_setup_logging,
    )

    monkeypatch.setattr(
        main_module,
        "EchoLLMProvider",
        FakeEchoLLMProvider,
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
        None,
    )

    assert calls[3][0] == "agent_init"
    assert calls[4][0] == "server_init"

    assert calls[5] == (
        "server_run",
        None,
    )
