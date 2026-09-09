import logging
from json import JSONDecodeError

from websockets.asyncio.server import ServerConnection, serve

from agent_core.core.agent import Agent
from agent_core.core.message import Message

logger = logging.getLogger(__name__)


class WebSocketServer:
    """
    Desktop Companion Agent 的本地 WebSocket 服务端。

    负责：
    - 启动服务器
    - 管理客户端连接生命周期
    - 接收协议消息
    - 调用 Agent
    - 返回 Agent 响应
    - 处理基础协议错误
    """

    def __init__(
        self,
        host: str,
        port: int,
        agent: Agent,
    ) -> None:
        self.host = host
        self.port = port
        self.agent = agent

    async def handle_connection(
        self,
        websocket: ServerConnection,
    ) -> None:
        """
        处理单个 WebSocket 客户端连接。
        """

        logger.info(
            "WebSocket client connected: %s",
            websocket.remote_address,
        )

        try:
            async for raw_message in websocket:
                response = await self._process_raw_message(
                    raw_message,
                )

                await websocket.send(
                    response.to_json(),
                )

        finally:
            logger.info(
                "WebSocket client disconnected: %s",
                websocket.remote_address,
            )

    async def _process_raw_message(
        self,
        raw_message: str | bytes,
    ) -> Message:
        """
        解析并处理一条原始 WebSocket 消息。

        无论输入是否合法，都返回一个协议 Message，
        避免单条坏消息中断整个客户端连接。
        """

        if isinstance(raw_message, bytes):
            logger.warning(
                "Received unsupported binary WebSocket message",
            )

            return Message(
                type="error",
                source="agent_core",
                payload={
                    "message": "Binary messages are not supported",
                },
            )

        try:
            message = Message.from_json(
                raw_message,
            )

        except JSONDecodeError:
            logger.warning(
                "Received invalid JSON message",
            )

            return Message(
                type="error",
                source="agent_core",
                payload={
                    "message": "Invalid JSON message",
                },
            )

        except (KeyError, TypeError):
            logger.warning(
                "Received invalid message structure",
            )

            return Message(
                type="error",
                source="agent_core",
                payload={
                    "message": "Invalid message structure",
                },
            )

        return await self.agent.process_message(
            message,
        )

    async def run(self) -> None:
        """
        启动 WebSocket Server，并持续运行。
        """

        logger.info(
            "Starting WebSocket server on %s:%s",
            self.host,
            self.port,
        )

        async with serve(
            self.handle_connection,
            self.host,
            self.port,
        ) as server:
            await server.serve_forever()
