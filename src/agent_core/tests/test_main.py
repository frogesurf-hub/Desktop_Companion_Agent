from agent_core import main as main_module


def test_main_initializes_runtime(
    monkeypatch,
) -> None:
    """
    验证 main() 会读取配置、初始化日志并输出启动信息。
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

    main_module.main()

    assert calls == [
        ("get_settings", None),
        ("setup_logging", "DEBUG"),
    ]
