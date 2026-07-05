from datetime import datetime
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field, TypeAdapter, ValidationError


class MediaItem(BaseModel):
    file_name: str
    download_url: str


class ConnectPacket(BaseModel):
    action: Literal["connect"] = "connect"
    username: str


class ActiveUsersPacket(BaseModel):
    action: Literal["active_users"] = "active_users"
    users: List[str] = []


class ChatMessagePacket(BaseModel):
    action: Literal["chat_message"] = "chat_message"
    message_type: Literal["text", "media"] = "text"
    username: str
    message: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M-%d/%m/%Y"))
    media_items: List[MediaItem] = []


AnyPacket = Annotated[
    Union[ConnectPacket, ActiveUsersPacket, ChatMessagePacket],
    Field(discriminator="action"),
]

_packet_adapter = TypeAdapter(AnyPacket)


def parse_packet(raw: Union[str, bytes]) -> Optional[AnyPacket]:
    """Parse and validate a raw JSON packet. Returns None on invalid input."""
    try:
        return _packet_adapter.validate_json(raw)
    except ValidationError:
        return None
