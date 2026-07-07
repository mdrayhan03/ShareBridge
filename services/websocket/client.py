import asyncio
import logging

import websockets

from services.schemas import ChatMessagePacket, ConnectPacket

log = logging.getLogger(__name__)


class MyClient:
    def __init__(self, host="127.0.0.1", port=8765):
        self.host = host
        self.port = port
        self.uri = None
        self.connection = None
        self.is_running = False
        self.on_message_callback = None
        self.on_connection_lost_callback = None

    def find_server_uri(self):
        """Builds the server URI."""
        return f"ws://{self.host}:{self.port}"

    async def connect(self, timeout=4.0):
        """Establishes the connection (with a timeout so it can't hang forever)."""
        self.uri = self.find_server_uri()
        try:
            self.connection = await asyncio.wait_for(
                websockets.connect(self.uri), timeout=timeout
            )
            log.info(f"Connected to {self.uri}")
            return True
        except Exception as e:
            log.error(f"Connection failed: {e}")
            return False

    async def receive_loop(self):
        """Listens for messages indefinitely."""
        try:
            while self.is_running:
                message = await self.connection.recv()
                if self.on_message_callback:
                    self.on_message_callback(message)
        except websockets.ConnectionClosed:
            log.info("Disconnected from server.")
            self.is_running = False
            if self.on_connection_lost_callback:
                self.on_connection_lost_callback()

    async def send_packet(self, packet):
        """Serializes and sends any schema packet."""
        if not self.connection:
            log.warning("Not connected to server.")
            return
        try:
            await self.connection.send(packet.model_dump_json())
        except websockets.ConnectionClosed:
            log.warning("Connection lost.")

    async def send_connect_message(self, username, fullname=""):
        """Sends the initial connection metadata."""
        await self.send_packet(ConnectPacket(username=username, fullname=fullname))

    async def send_message(self, username, message):
        """Sends a plain text chat message."""
        await self.send_packet(ChatMessagePacket(username=username, message=message))

    async def close(self):
        """Closes the connection safely."""
        if self.connection:
            await self.connection.close()
            log.info("Client closed.")
