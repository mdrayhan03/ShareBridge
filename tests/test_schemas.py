from services.schemas import (
    ActiveUsersPacket,
    ChatMessagePacket,
    ConnectPacket,
    MediaItem,
    parse_packet,
)


def test_valid_chat_message_parses():
    raw = ChatMessagePacket(username="ray", message="hi").model_dump_json()
    packet = parse_packet(raw)
    assert isinstance(packet, ChatMessagePacket)
    assert packet.username == "ray"
    assert packet.message == "hi"
    assert packet.message_type == "text"


def test_media_message_roundtrip():
    original = ChatMessagePacket(
        username="ray",
        message_type="media",
        media_items=[MediaItem(file_name="a.zip", download_url="http://x:8080/download/abc")],
    )
    packet = parse_packet(original.model_dump_json())
    assert isinstance(packet, ChatMessagePacket)
    assert packet.media_items[0].file_name == "a.zip"


def test_connect_packet_parses():
    packet = parse_packet('{"action": "connect", "username": "ray"}')
    assert isinstance(packet, ConnectPacket)
    assert packet.username == "ray"


def test_active_users_packet_parses():
    packet = parse_packet('{"action": "active_users", "users": ["a", "b"]}')
    assert isinstance(packet, ActiveUsersPacket)
    assert packet.users == ["a", "b"]


def test_garbage_returns_none():
    assert parse_packet("not json") is None
    assert parse_packet('{"action": "unknown"}') is None
    assert parse_packet('{"action": "connect"}') is None  # missing username
    assert parse_packet('{}') is None
