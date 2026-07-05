import asyncio
import logging

import websockets

from services.schemas import (
    ActiveUsersPacket,
    ChatMessagePacket,
    ConnectPacket,
    parse_packet,
)

log = logging.getLogger(__name__)


class MyServer:
    def __init__(self):
        self.server = None
        self.loop = None
        self.stop_event = None
        # Map websocket -> username
        self.connected_clients = {}

    async def broadcast_active_users(self):
        packet = ActiveUsersPacket(users=list(self.connected_clients.values()))
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
                    self.connected_clients[websocket] = packet.username
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
