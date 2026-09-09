import asyncio
import logging
import socket
from contextlib import suppress

import pytest
from websockets.asyncio.client import ClientConnection, connect

from agent_core.communication import WebSocketServer
from agent_core.core.agent import Agent
from agent_core.core.message import Message
from agent_core.providers import LLMResponse
from agent_core.tests.fakes import FakeLLMProvider


def _get_free_port() -> int:
    """
    从操作系统获取一个当前可用的本地端口。
    """

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    assert isinstance(port, int)

    return port


def _create_agent(
    response_text: str = "fake response",
) -> Agent:
    """
    创建注入确定性 Fake Provider 的测试 Agent。
    """

    provider = FakeLLMProvider(
        response=LLMResponse(
            content=response_text,
        ),
    )

    return Agent(
        provider=provider,
    )


async def _connect_with_retry(
    uri: str,
) -> ClientConnection:
    """
    等待 WebSocket Server 启动并建立连接。
    """

    last_error: OSError | None = None

    for _ in range(50):
        try:
            return await connect(
                uri,
                proxy=None,
            )
        except OSError as exc:
            last_error = exc
            await asyncio.sleep(0.01)

    raise AssertionError(
        "WebSocket server did not start in time"
    ) from last_error


def test_websocket_server_connection_lifecycle(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    验证 WebSocket Server 能够：

    1. 启动监听
    2. 接受客户端连接
    3. 正常处理客户端断开
    4. 在客户端断开后继续运行
    """

    caplog.set_level(
        logging.INFO,
        logger="agent_core.communication.websocket_server",
    )

    async def scenario() -> None:
        port = _get_free_port()

        server = WebSocketServer(
            host="127.0.0.1",
            port=port,
            agent=_create_agent(),
        )

        server_task = asyncio.create_task(
            server.run(),
        )

        try:
            client = await _connect_with_retry(
                f"ws://127.0.0.1:{port}"
            )

            await client.close()

            for _ in range(50):
                if (
                    "WebSocket client disconnected:"
                    in caplog.text
                ):
                    break

                await asyncio.sleep(0.01)

            assert (
                "WebSocket client connected:"
                in caplog.text
            )

            assert (
                "WebSocket client disconnected:"
                in caplog.text
            )

            assert not server_task.done()

        finally:
            server_task.cancel()

            with suppress(asyncio.CancelledError):
                await server_task

    asyncio.run(scenario())


def test_websocket_server_message_round_trip() -> None:
    """
    验证客户端发送 chat Message 后，
    WebSocket Server 会等待 Agent 并返回 Provider 响应。
    """

    async def scenario() -> None:
        port = _get_free_port()

        server = WebSocketServer(
            host="127.0.0.1",
            port=port,
            agent=_create_agent(
                response_text="来自 Provider 的 WebSocket 回复",
            ),
        )

        server_task = asyncio.create_task(
            server.run(),
        )

        try:
            client = await _connect_with_retry(
                f"ws://127.0.0.1:{port}"
            )

            message = Message(
                type="chat",
                source="desktop",
                payload={
                    "message": "你好",
                },
            )

            await client.send(
                message.to_json(),
            )

            raw_response = await client.recv()

            assert isinstance(
                raw_response,
                str,
            )

            response = Message.from_json(
                raw_response,
            )

            assert response.type == "response"

            assert (
                response.payload["message"]
                == "来自 Provider 的 WebSocket 回复"
            )

            await client.close()

        finally:
            server_task.cancel()

            with suppress(asyncio.CancelledError):
                await server_task

    asyncio.run(scenario())


def test_websocket_server_rejects_invalid_json() -> None:
    """
    验证非法 JSON 会返回 error Message，
    而不是关闭 WebSocket 连接。
    """

    async def scenario() -> None:
        port = _get_free_port()

        server = WebSocketServer(
            host="127.0.0.1",
            port=port,
            agent=_create_agent(),
        )

        server_task = asyncio.create_task(
            server.run(),
        )

        try:
            client = await _connect_with_retry(
                f"ws://127.0.0.1:{port}"
            )

            await client.send(
                "this is not json",
            )

            raw_response = await client.recv()

            assert isinstance(
                raw_response,
                str,
            )

            response = Message.from_json(
                raw_response,
            )

            assert response.type == "error"

            assert (
                response.payload["message"]
                == "Invalid JSON message"
            )

            await client.close()

        finally:
            server_task.cancel()

            with suppress(asyncio.CancelledError):
                await server_task

    asyncio.run(scenario())


def test_websocket_server_rejects_invalid_message_structure() -> None:
    """
    验证缺少协议字段的 JSON 会返回 error Message。
    """

    async def scenario() -> None:
        port = _get_free_port()

        server = WebSocketServer(
            host="127.0.0.1",
            port=port,
            agent=_create_agent(),
        )

        server_task = asyncio.create_task(
            server.run(),
        )

        try:
            client = await _connect_with_retry(
                f"ws://127.0.0.1:{port}"
            )

            await client.send(
                '{"type": "chat"}',
            )

            raw_response = await client.recv()

            assert isinstance(
                raw_response,
                str,
            )

            response = Message.from_json(
                raw_response,
            )

            assert response.type == "error"

            assert (
                response.payload["message"]
                == "Invalid message structure"
            )

            await client.close()

        finally:
            server_task.cancel()

            with suppress(asyncio.CancelledError):
                await server_task

    asyncio.run(scenario())


def test_websocket_server_rejects_binary_message() -> None:
    """
    验证 Binary WebSocket 消息会返回协议错误。
    """

    async def scenario() -> None:
        port = _get_free_port()

        server = WebSocketServer(
            host="127.0.0.1",
            port=port,
            agent=_create_agent(),
        )

        server_task = asyncio.create_task(
            server.run(),
        )

        try:
            client = await _connect_with_retry(
                f"ws://127.0.0.1:{port}"
            )

            await client.send(
                b"binary-message",
            )

            raw_response = await client.recv()

            assert isinstance(
                raw_response,
                str,
            )

            response = Message.from_json(
                raw_response,
            )

            assert response.type == "error"

            assert (
                response.payload["message"]
                == "Binary messages are not supported"
            )

            await client.close()

        finally:
            server_task.cancel()

            with suppress(asyncio.CancelledError):
                await server_task

    asyncio.run(scenario())


def test_websocket_connection_survives_invalid_message() -> None:
    """
    验证客户端发送非法消息后，
    同一个 WebSocket 连接仍然可以继续处理正常消息。
    """

    async def scenario() -> None:
        port = _get_free_port()

        server = WebSocketServer(
            host="127.0.0.1",
            port=port,
            agent=_create_agent(
                response_text="连接仍然可用",
            ),
        )

        server_task = asyncio.create_task(
            server.run(),
        )

        try:
            client = await _connect_with_retry(
                f"ws://127.0.0.1:{port}"
            )

            # 先发送非法 JSON。
            await client.send(
                "invalid-json",
            )

            raw_error = await client.recv()

            assert isinstance(
                raw_error,
                str,
            )

            error_response = Message.from_json(
                raw_error,
            )

            assert error_response.type == "error"

            # 再通过同一个连接发送合法消息。
            message = Message(
                type="chat",
                source="desktop",
                payload={
                    "message": "连接还活着吗",
                },
            )

            await client.send(
                message.to_json(),
            )

            raw_response = await client.recv()

            assert isinstance(
                raw_response,
                str,
            )

            response = Message.from_json(
                raw_response,
            )

            assert response.type == "response"

            assert response.payload["message"] == "连接仍然可用"

            await client.close()

        finally:
            server_task.cancel()

            with suppress(asyncio.CancelledError):
                await server_task

    asyncio.run(scenario())
