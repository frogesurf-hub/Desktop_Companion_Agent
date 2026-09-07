from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any
import uuid
import json


@dataclass
class Message:
    """
    Agent系统内部统一消息模型
    """

    type: str
    source: str
    payload: Dict[str, Any]

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


    def to_json(self) -> str:
        """
        转换为JSON字符串
        """

        data = {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp,
            "source": self.source,
            "payload": self.payload
        }

        return json.dumps(
            data,
            ensure_ascii=False,
            indent=4
        )


    @classmethod
    def from_json(cls, data: str):
        """
        从JSON恢复Message对象
        """

        obj = json.loads(data)

        return cls(
            id=obj["id"],
            type=obj["type"],
            timestamp=obj["timestamp"],
            source=obj["source"],
            payload=obj["payload"]
        )