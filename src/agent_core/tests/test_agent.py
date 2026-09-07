from agent_core.core.agent import Agent
from agent_core.core.message import Message


def test_message_create() -> None:
    """
    测试 Message 是否可以正常创建。
    """

    message = Message(
        type="chat",
        source="desktop",
        payload={
            "message": "你好",
        },
    )

    assert message.type == "chat"
    assert message.source == "desktop"
    assert message.payload["message"] == "你好"


def test_message_json() -> None:
    """
    测试 Message JSON 转换。
    """

    message = Message(
        type="chat",
        source="desktop",
        payload={
            "message": "hello",
        },
    )

    json_data = message.to_json()

    restored = Message.from_json(json_data)

    assert restored.type == "chat"
    assert restored.payload["message"] == "hello"


def test_agent_response() -> None:
    """
    测试 Agent 处理消息。
    """

    agent = Agent()

    message = Message(
        type="chat",
        source="desktop",
        payload={
            "message": "你好",
        },
    )

    response = agent.process_message(message)

    assert response.type == "response"
    assert response.payload["message"] == "收到你的消息: 你好"
