import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Message:
    """
    Agent 系统内部统一消息模型。
    """

    type: str
    source: str
    payload: dict[str, Any]

    id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_json(self) -> str:
        """
        将 Message 转换为 JSON 字符串。
        """

        data = {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp,
            "source": self.source,
            "payload": self.payload,
        }

        return json.dumps(
            data,
            ensure_ascii=False,
            indent=4,
        )

    @classmethod
    def from_json(cls, data: str) -> "Message":
        """
        从 JSON 字符串恢复 Message 对象。
        """

        obj = json.loads(data)

        return cls(
            id=obj["id"],
            type=obj["type"],
            timestamp=obj["timestamp"],
            source=obj["source"],
            payload=obj["payload"],
        )
