import asyncio
import logging
import socket
from contextlib import suppress

import pytest
from websockets.asyncio.client import ClientConnection, connect

from agent_core.communication import WebSocketServer


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


async def _connect_with_retry(
    uri: str,
) -> ClientConnection:
    """
    等待 WebSocket Server 启动并建立连接。

    Server 和 Client 是并发启动的，因此允许短时间重试，
    避免测试依赖固定的 sleep 时间。
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
