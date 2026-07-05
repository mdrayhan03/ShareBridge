# 🩺 ShareBridge — Known Issues & Solution Plan

> **✅ STATUS: All 10 issues below were fixed on 2026-07-05.**
> This document is kept as a record of the problems and the reasoning behind
> the fixes. Covered by the test suite in `tests/` (`pytest tests/`).
>
> Severity legend: 🔴 Critical · 🟡 Medium · 🟢 Minor
>
> One deviation from the original plan: the Android background service
> (`service.py`) no longer starts the HTTP file server — the file server runs
> in the app process on **every** peer, because the file token registry
> (Issue #1) must live in the same process as the UI that registers files.

---

## Issue #1 🔴 — Path traversal: any LAN device can download ANY file

**Where:** `services/http_server.py` (`download_handler`)

**Problem:**
The download route serves whatever path appears in the URL:

```
GET http://<host>:8080/download/Users/you/.ssh/id_rsa
GET http://<host>:8080/download/etc/passwd
```

Both work. Anyone on the same Wi-Fi can read any file the app's user can read.
Bonus problem: the full local filesystem path of every shared file is leaked to
every chat member inside the `download_url`.

**Solution — token-based file registry:**
Never accept a filesystem path from the network. When the user attaches a file,
register it under a random token and only serve registered tokens.

```python
# services/http_server.py
import os
import uuid
import asyncio
from aiohttp import web

class FileTransferServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.shared_files = {}   # token -> absolute file path
        self.app = web.Application()
        self.app.router.add_get('/download/{token}', self.download_handler)

    def register_file(self, file_path: str) -> str:
        """Call this when the user attaches a file. Returns the URL token."""
        token = uuid.uuid4().hex
        self.shared_files[token] = os.path.abspath(file_path)
        return token

    async def download_handler(self, request):
        token = request.match_info['token']

        # Only files the user explicitly attached are downloadable.
        file_path = self.shared_files.get(token)
        if not file_path or not os.path.isfile(file_path):
            raise web.HTTPNotFound(text="File not found")

        file_size = os.path.getsize(file_path)

        response = web.StreamResponse()
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = (
            f'attachment; filename="{os.path.basename(file_path)}"'
        )
        response.headers['Content-Length'] = str(file_size)
        await response.prepare(request)

        loop = asyncio.get_running_loop()
        try:
            with open(file_path, 'rb') as f:
                chunk_size = 1024 * 1024 * 2  # 2MB chunks
                while True:
                    chunk = await loop.run_in_executor(None, f.read, chunk_size)
                    if not chunk:
                        break
                    await response.write(chunk)
        except ConnectionResetError:
            pass  # Client disconnected early
        return response
```

Then in `src/pages/InboxPage.py` (`send_message_logic`), build URLs from
tokens instead of raw paths:

```python
token = self.app.http_server.register_file(file_path)
download_url = f"http://{host_ip}:8080/download/{token}"
```

**Result:** attackers can only fetch files the user deliberately shared, and
local paths never leave the machine.

---

## Issue #2 🔴 — File sharing is broken for non-host clients

**Where:** `MainApplication.py` (`_async_start_host` / `connect_as_client`),
`src/pages/InboxPage.py`

**Problem:**
Only the **host** ever starts `FileTransferServer` (inside
`_async_start_host`). But *every* sender builds a `download_url` pointing at
**their own** `IP:8080`. So when a non-host client shares a file, receivers get
a dead link — nothing is listening on port 8080 on that machine.

**Solution — every peer runs its own file server (P2P model):**
Files stay on the sender's machine and are fetched directly from it. Start the
HTTP server for *everyone* in `connect_as_client`, not just the host:

```python
# MainApplication.py
async def connect_as_client(self, ip):
    from services.websocket.client import MyClient

    # EVERY peer serves its own shared files.
    if not getattr(self, "http_server", None):
        from services.http_server import FileTransferServer
        self.http_server = FileTransferServer()
        asyncio.create_task(self.http_server.start())

    self.client = MyClient(host=ip)
    ...
```

And remove the now-duplicated startup from `_async_start_host` (the host will
get its file server through `connect_as_client("127.0.0.1")` like everyone
else).

> Alternative considered: upload files to the host first and let the host serve
> them. Simpler URLs, but doubles the transfer (client → host → client) and
> fills the host's disk. For a LAN tool, the P2P model above is better.

**Result:** any participant can share files, not just the host.

---

## Issue #3 🔴 — Pydantic schemas exist but are never used (protocol drift)

**Where:** `services/schemas.py` (never imported anywhere),
`services/websocket/server.py`, `services/websocket/client.py`,
`src/pages/InboxPage.py`

**Problem:**
The README advertises strict Pydantic validation, but every packet is a
hand-built dict. The protocol has already drifted because of it:

- two action names for the same thing: `"message"` vs `"chat_message"`
- two field names for the body: `"content"` vs `"message"`
- back-compat shims in the UI (`data.get("message", data.get("content"))`)

**Solution — one schema module, used at every boundary:**

**Step 1.** Extend `services/schemas.py` to cover *all* packet types and add a
single parse helper:

```python
# services/schemas.py
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Literal, List, Union
from datetime import datetime

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
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%H:%M-%d/%m/%Y")
    )
    media_items: List[MediaItem] = []

AnyPacket = Union[ConnectPacket, ActiveUsersPacket, ChatMessagePacket]

def parse_packet(raw: str) -> Optional[AnyPacket]:
    """Parse+validate a raw JSON string. Returns None on invalid input."""
    from pydantic import TypeAdapter
    try:
        return TypeAdapter(AnyPacket).validate_json(raw)
    except ValidationError:
        return None
```

**Step 2.** Server validates before relaying (`services/websocket/server.py`):

```python
from services.schemas import parse_packet, ConnectPacket, ChatMessagePacket, ActiveUsersPacket

async def broadcast_handler(self, websocket):
    try:
        async for raw in websocket:
            packet = parse_packet(raw)
            if packet is None:
                continue  # drop malformed packets

            if isinstance(packet, ConnectPacket):
                self.connected_clients[websocket] = packet.username
                await self.broadcast_active_users()

            elif isinstance(packet, ChatMessagePacket):
                out = packet.model_dump_json()
                for client in list(self.connected_clients):
                    if client != websocket:
                        try:
                            await client.send(out)
                        except websockets.ConnectionClosed:
                            pass
    finally:
        ...
```

**Step 3.** Client sends only schema objects (`services/websocket/client.py`):

```python
from services.schemas import ChatMessagePacket, ConnectPacket

async def send_message(self, username, message):
    if self.connection:
        packet = ChatMessagePacket(username=username, message=message)
        await self.connection.send(packet.model_dump_json())
```

**Step 4.** Delete the legacy branches: the `"message"` action and `"content"`
field handling in `InboxPage.process_incoming_msg` / `add_message_to_ui`, and
the `("message", "chat_message")` tuple in the server. One action name, one
field name, everywhere.

**Result:** malformed packets can't crash the UI, and the protocol has a single
source of truth.

---

## Issue #4 🟡 — `gethostbyname(gethostname())` returns the wrong IP

**Where:** `src/pages/InboxPage.py` (`send_message_logic`),
`services/websocket/get_server_ip.py`

**Problem:**
`socket.gethostbyname(socket.gethostname())` frequently returns `127.0.0.1`
(macOS/Linux with default `/etc/hosts`) or the wrong interface's address. A
`download_url` built from `127.0.0.1` is useless to other devices.

**Solution — the UDP-connect trick** (no packet is actually sent; the OS just
picks the outbound interface):

```python
# services/websocket/get_server_ip.py
import socket

def get_lan_ip() -> str:
    """Return this machine's LAN IP (the interface used to reach the network)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))   # no traffic sent — just routes the socket
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()
```

Use `get_lan_ip()` in `send_message_logic` instead of the
`gethostbyname` call.

---

## Issue #5 🟡 — `stop_server_logic` crashes if server never started

**Where:** `services/websocket/server.py`

**Problem:** `self.stop_event` is only created inside `main_serve()`. Calling
`stop_server_logic()` before (or without) starting raises `AttributeError`.

**Solution:** create the event in `__init__` and guard the stop call:

```python
class MyServer:
    def __init__(self):
        self.server = None
        self.loop = None
        self.stop_event = None
        self.connected_clients = {}

    async def main_serve(self):
        self.stop_event = asyncio.Event()
        ...

    def stop_server_logic(self):
        if self.loop and self.loop.is_running() and self.stop_event:
            self.loop.call_soon_threadsafe(self.stop_event.set)
```

---

## Issue #6 🟡 — Sidebar items built from f-string KV (injection-prone)

**Where:** `src/pages/InboxPage.py` (`update_active_users`)

**Problem:** usernames are interpolated into KV source and compiled with
`Builder.load_string`. A username containing `\n` or KV syntax breaks (or
alters) the layout — the `"` escaping isn't enough.

**Solution:** build the widgets in Python; data stays data:

```python
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemHeadlineText

def update_active_users(self, data):
    users = data.get("users", [])
    menu = self.ids.active_users_menu
    menu.clear_widgets()
    for user in users:
        menu.add_widget(
            MDListItem(
                MDListItemLeadingIcon(icon="account-circle"),
                MDListItemHeadlineText(text=str(user)),
            )
        )
```

---

## Issue #7 🟢 — Dead code committed

**Where:** `services/websocket_backup/`, `services/websocket/test.py`,
`MyClient.on_message_received` (never called), commented-out example block at
the bottom of `client.py`.

**Solution:** delete them. Git history keeps everything; a "backup" folder in
the working tree only confuses readers (and yourself in six months).

```bash
git rm -r services/websocket_backup services/websocket/test.py
```

---

## Issue #8 🟢 — `print()` instead of logging

**Where:** everywhere.

**Solution:** use Kivy's logger — it shows up in Android logcat too:

```python
from kivy.logger import Logger

Logger.info("UDP: Searching local network for ShareBridge server...")
Logger.error(f"Network: Connection failed: {e}")
```

Mechanical find-and-replace; do it file by file as you touch them.

---

## Issue #9 🟢 — Unpinned KivyMD dependency

**Where:** `requirements.txt`

**Problem:** `kivymd @ .../master.zip` means every install may pull different
code — builds are not reproducible and can break overnight.

**Solution:** pin to a specific commit:

```
kivymd @ https://github.com/kivymd/KivyMD/archive/<commit-sha>.zip
```

Find the sha of the version that currently works:
`pip show kivymd` → or check `venv/lib/.../kivymd/__init__.py` /
the KivyMD repo's commit list, then pin it.

---

## Issue #10 🟢 — No tests

**Problem:** the protocol layer (schemas, server broadcast, discovery parsing)
is pure logic and very testable, but nothing is tested.

**Solution:** start small — a `tests/` folder with pytest covering the pieces
that don't need a UI:

```python
# tests/test_schemas.py
from services.schemas import parse_packet, ChatMessagePacket

def test_valid_chat_message_parses():
    raw = ChatMessagePacket(username="ray", message="hi").model_dump_json()
    packet = parse_packet(raw)
    assert isinstance(packet, ChatMessagePacket)
    assert packet.message == "hi"

def test_garbage_returns_none():
    assert parse_packet("not json") is None
    assert parse_packet('{"action": "unknown"}') is None
```

```python
# tests/test_file_registry.py
from services.http_server import FileTransferServer

def test_register_returns_unique_tokens(tmp_path):
    f = tmp_path / "a.txt"; f.write_text("x")
    srv = FileTransferServer()
    t1, t2 = srv.register_file(str(f)), srv.register_file(str(f))
    assert t1 != t2
    assert srv.shared_files[t1] == str(f)
```

Run with `pip install pytest` → `pytest tests/`.

---

## ✅ Suggested execution order

| Step | Issue | Effort | Files touched |
|------|-------|--------|---------------|
| 1 | #1 Token-based downloads | ~1h | `http_server.py`, `InboxPage.py` |
| 2 | #2 File server on every peer | ~30m | `MainApplication.py` |
| 3 | #3 Pydantic everywhere | ~2h | `schemas.py`, `server.py`, `client.py`, `InboxPage.py` |
| 4 | #4 LAN IP helper | ~15m | `get_server_ip.py`, `InboxPage.py` |
| 5 | #5 Safe server stop | ~10m | `server.py` |
| 6 | #6 Python-built list items | ~20m | `InboxPage.py` |
| 7 | #7 Delete dead code | ~5m | — |
| 8 | #8 Logging | ongoing | all |
| 9 | #9 Pin KivyMD | ~5m | `requirements.txt` |
| 10 | #10 First tests | ~1h | `tests/` |

After steps 1–3, test the full flow on two devices: host + client, share a file
in **both directions**, and confirm a made-up URL like
`/download/anything` returns 404.
