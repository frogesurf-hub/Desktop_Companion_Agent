import logging

from websockets.asyncio.server import ServerConnection, serve

logger = logging.getLogger(__name__)


class WebSocketServer:
    """
    Desktop Companion Agent 的本地 WebSocket 服务端。

    当前阶段只负责：
    - 启动服务器
    - 接受客户端连接
    - 维护连接生命周期

    后续阶段再加入消息解析与 Agent 调用。
    """

    def __init__(
        self,
        host: str,
        port: int,
    ) -> None:
        self.host = host
        self.port = port

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
            async for _message in websocket:
                pass
        finally:
            logger.info(
                "WebSocket client disconnected: %s",
                websocket.remote_address,
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
