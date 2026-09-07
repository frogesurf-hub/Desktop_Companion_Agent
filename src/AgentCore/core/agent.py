from AgentCore.core.message import Message


class Agent:
    """
    Agent核心逻辑

    当前版本：
    接收消息
    返回简单回复

    后续：
    接入LLM、Memory、Tool等模块
    """


    def __init__(self, name: str = "Desktop Companion"):
        self.name = name


    def process_message(self, message: Message) -> Message:
        """
        处理输入消息

        输入:
            Message

        输出:
            Message
        """


        if message.type == "chat":

            user_text = message.payload.get(
                "message",
                ""
            )


            response_text = (
                f"收到你的消息: {user_text}"
            )


            return Message(
                type="response",
                source=self.name,
                payload={
                    "message": response_text
                }
            )


        return Message(
            type="error",
            source=self.name,
            payload={
                "message": "Unsupported message type"
            }
        )