"""Network packet schemas — pure Python, no third-party dependency.

Deliberately dependency-free so the app packages cleanly on every platform
(including Android via python-for-android, which cannot cross-compile a native
validation library). Each packet validates its own fields on construction and
`parse_packet` drops anything malformed, so the protocol layer never crashes on
bad input.
"""
import json
from datetime import datetime


def _now_timestamp():
    return datetime.now().strftime("%H:%M-%d/%m/%Y")


class _Packet:
    """Base: JSON serialization on top of a dict produced by model_dump()."""

    def model_dump(self):
        raise NotImplementedError

    def model_dump_json(self):
        return json.dumps(self.model_dump())


class MediaItem(_Packet):
    def __init__(self, file_name, download_url):
        if not isinstance(file_name, str) or not isinstance(download_url, str):
            raise ValueError("MediaItem fields must be strings")
        self.file_name = file_name
        self.download_url = download_url

    def model_dump(self):
        return {"file_name": self.file_name, "download_url": self.download_url}


class ConnectPacket(_Packet):
    action = "connect"

    def __init__(self, username):
        if not isinstance(username, str):
            raise ValueError("username must be a string")
        self.username = username

    def model_dump(self):
        return {"action": "connect", "username": self.username}


class ActiveUsersPacket(_Packet):
    action = "active_users"

    def __init__(self, users=None):
        users = users if users is not None else []
        if not isinstance(users, list) or not all(isinstance(u, str) for u in users):
            raise ValueError("users must be a list of strings")
        self.users = users

    def model_dump(self):
        return {"action": "active_users", "users": list(self.users)}


class ChatMessagePacket(_Packet):
    action = "chat_message"

    def __init__(self, username, message="", message_type="text",
                 media_items=None, timestamp=None):
        if not isinstance(username, str):
            raise ValueError("username must be a string")
        if message_type not in ("text", "media"):
            raise ValueError("message_type must be 'text' or 'media'")
        self.username = username
        self.message = message if isinstance(message, str) else ""
        self.message_type = message_type
        self.timestamp = timestamp if isinstance(timestamp, str) else _now_timestamp()

        items = media_items if media_items is not None else []
        if not isinstance(items, list):
            raise ValueError("media_items must be a list")
        self.media_items = []
        for it in items:
            if isinstance(it, MediaItem):
                self.media_items.append(it)
            elif isinstance(it, dict):
                self.media_items.append(
                    MediaItem(it.get("file_name", ""), it.get("download_url", ""))
                )
            else:
                raise ValueError("media_items entries must be MediaItem or dict")

    def model_dump(self):
        return {
            "action": "chat_message",
            "message_type": self.message_type,
            "username": self.username,
            "message": self.message,
            "timestamp": self.timestamp,
            "media_items": [m.model_dump() for m in self.media_items],
        }


def parse_packet(raw):
    """Parse and validate a raw JSON packet. Returns a packet or None if invalid."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None

    action = data.get("action")
    try:
        if action == "connect":
            return ConnectPacket(username=data["username"])
        if action == "active_users":
            return ActiveUsersPacket(users=data.get("users", []))
        if action == "chat_message":
            return ChatMessagePacket(
                username=data["username"],
                message=data.get("message", ""),
                message_type=data.get("message_type", "text"),
                media_items=data.get("media_items", []),
                timestamp=data.get("timestamp"),
            )
    except (KeyError, ValueError, TypeError):
        return None
    return None
