import asyncio
import socket
from contextlib import suppress

from websockets.asyncio.client import (
    ClientConnection,
    connect,
)

from agent_core.communication import WebSocketServer
from agent_core.core.message import Message
from agent_core.providers import (
    LLMRequest,
    LLMResponse,
    ProviderTimeoutError,
)
from agent_core.tests.fakes import create_test_agent


class FailThenSucceedProvider:
    """
    第一次调用失败，第二次调用成功。

    用于验证 Provider failure
    不会破坏当前 WebSocket 连接。
    """

    def __init__(self) -> None:
        self.calls = 0
        self.requests: list[LLMRequest] = []

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        self.calls += 1

        self.requests.append(
            request,
        )

        if self.calls == 1:
            raise ProviderTimeoutError(
                "internal timeout diagnostic",
            )

        return LLMResponse(
            content="recovered response",
        )


def _get_free_port() -> int:
    """
    从操作系统获取一个当前可用的本地端口。
    """

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:
        sock.bind(
            (
                "127.0.0.1",
                0,
            )
        )

        port = sock.getsockname()[1]

    assert isinstance(
        port,
        int,
    )

    return port


async def _connect_with_retry(
    uri: str,
) -> ClientConnection:
    """
    等待 WebSocket Server 启动。
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

            await asyncio.sleep(
                0.01,
            )

    raise AssertionError(
        "WebSocket server did not start in time"
    ) from last_error


def test_websocket_connection_survives_provider_failure() -> None:
    """
    验证：

    Provider failure
    -> protocol error
    -> 同一个 WebSocket 连接仍可继续处理下一条请求。
    """

    async def scenario() -> None:
        port = _get_free_port()

        provider = FailThenSucceedProvider()

        agent = create_test_agent(
            provider,
        )

        server = WebSocketServer(
            host="127.0.0.1",
            port=port,
            agent=agent,
        )

        server_task = asyncio.create_task(
            server.run(),
        )

        try:
            client = await _connect_with_retry(
                f"ws://127.0.0.1:{port}",
            )

            first_message = Message(
                type="chat",
                source="desktop",
                payload={
                    "message": "first request",
                },
            )

            await client.send(
                first_message.to_json(),
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

            assert error_response.payload == {
                "code": "PROVIDER_TIMEOUT",
                "message": "AI provider request timed out.",
            }

            assert (
                "internal timeout diagnostic"
                not in raw_error
            )

            second_message = Message(
                type="chat",
                source="desktop",
                payload={
                    "message": "second request",
                },
            )

            await client.send(
                second_message.to_json(),
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
                == "recovered response"
            )

            assert provider.calls == 2

            await client.close()

        finally:
            server_task.cancel()

            with suppress(
                asyncio.CancelledError,
            ):
                await server_task

    asyncio.run(
        scenario(),
    )
