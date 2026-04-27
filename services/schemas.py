from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime

class BasePacket(BaseModel):
    action: str

class MediaItem(BaseModel):
    file_name: str
    download_url: str

class ChatMessagePacket(BasePacket):
    action: Literal["chat_message"] = "chat_message"
    message_type: Literal["text", "media"]
    username: str
    message: Optional[str] = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M-%d/%m/%Y"))
    
    # Media specific fields
    media_items: Optional[List[MediaItem]] = []
