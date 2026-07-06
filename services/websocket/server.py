import asyncio
import logging

import websockets

from services.schemas import (
    ActiveUsersPacket,
    ChatMessagePacket,
    ConnectPacket,
    UserInfo,
    parse_packet,
)

log = logging.getLogger(__name__)


class MyServer:
    def __init__(self):
        self.server = None
        self.loop = None
        self.stop_event = None
        # Map websocket -> UserInfo
        self.connected_clients = {}
        # The first client to connect is the host (it's the host device's own
        # client connecting to its server). Used to tag "(Host)" in the UI.
        self.host_ws = None
        # This machine's LAN IP, resolved once and shared with clients.
        self.server_ip = ""

    async def broadcast_active_users(self):
        if not self.server_ip:
            try:
                from services.websocket.get_server_ip import get_lan_ip
                self.server_ip = get_lan_ip()
            except Exception:
                self.server_ip = ""
        host_username = ""
        if self.host_ws is not None and self.host_ws in self.connected_clients:
            host_username = self.connected_clients[self.host_ws].username
        packet = ActiveUsersPacket(
            users=list(self.connected_clients.values()),
            host=host_username,
            server_ip=self.server_ip,
        )
        message = packet.model_dump_json()
        for client in list(self.connected_clients.keys()):
            try:
                await client.send(message)
            except websockets.ConnectionClosed:
                pass

    async def broadcast_handler(self, websocket):
        """Receives a message and handles it."""
        try:
            async for raw in websocket:
                packet = parse_packet(raw)
                if packet is None:
                    log.warning("Dropping malformed packet")
                    continue

                if isinstance(packet, ConnectPacket):
                    self.connected_clients[websocket] = UserInfo(
                        packet.username, packet.fullname
                    )
                    if self.host_ws is None:
                        self.host_ws = websocket
                    await self.broadcast_active_users()

                elif isinstance(packet, ChatMessagePacket):
                    # Broadcast to everyone else
                    out_msg = packet.model_dump_json()
                    for client in list(self.connected_clients.keys()):
                        if client != websocket:
                            try:
                                await client.send(out_msg)
                            except websockets.ConnectionClosed:
                                pass
        finally:
            if websocket in self.connected_clients:
                del self.connected_clients[websocket]
                if websocket == self.host_ws:
                    self.host_ws = None
                await self.broadcast_active_users()

    async def main_serve(self):
        self.stop_event = asyncio.Event()
        async with websockets.serve(self.broadcast_handler, "0.0.0.0", 8765) as server:
            self.server = server
            log.info("Server started and listening on port 8765")
            await self.stop_event.wait()

    def start_server_logic(self):
        """This runs in a background thread so it doesn't freeze your app UI"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.loop.run_until_complete(self.main_serve())

    def stop_server_logic(self):
        """This is what your 'Stop' button calls"""
        if self.loop and self.loop.is_running() and self.stop_event:
            log.info("Stopping server...")
            self.loop.call_soon_threadsafe(self.stop_event.set)
