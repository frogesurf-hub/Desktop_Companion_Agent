from AgentCore.core.message import Message
from AgentCore.core.agent import Agent


def test_message_create():
    """
    测试Message是否可以正常创建
    """

    message = Message(
        type="chat",
        source="desktop",
        payload={
            "message": "你好"
        }
    )


    assert message.type == "chat"
    assert message.source == "desktop"
    assert message.payload["message"] == "你好"



def test_message_json():

    """
    测试Message JSON转换
    """

    message = Message(
        type="chat",
        source="desktop",
        payload={
            "message": "hello"
        }
    )


    json_data = message.to_json()


    restored = Message.from_json(
        json_data
    )


    assert restored.type == "chat"
    assert restored.payload["message"] == "hello"



def test_agent_response():

    """
    测试Agent处理消息
    """

    agent = Agent()


    message = Message(
        type="chat",
        source="desktop",
        payload={
            "message": "你好"
        }
    )


    response = agent.process_message(
        message
    )


    assert response.type == "response"

    assert (
        response.payload["message"]
        ==
        "收到你的消息: 你好"
    )