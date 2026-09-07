from agent_core.core.message import Message


class Agent:
    """
    Agent 核心逻辑。

    当前版本：
    接收消息并返回简单回复。

    后续会接入：
    - LLM
    - Memory
    - Behavior
    - Tool
    """

    def __init__(self, name: str = "Desktop Companion") -> None:
        self.name = name

    def process_message(self, message: Message) -> Message:
        """
        处理输入消息并返回统一 Message。
        """

        if message.type == "chat":
            user_text = message.payload.get("message", "")

            response_text = f"收到你的消息: {user_text}"

            return Message(
                type="response",
                source=self.name,
                payload={
                    "message": response_text,
                },
            )

        return Message(
            type="error",
            source=self.name,
            payload={
                "message": "Unsupported message type",
            },
        )
