import asyncio
import websockets

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

    async def connect(self):
        """Establishes the connection."""
        self.uri = self.find_server_uri()
        try:
            self.connection = await websockets.connect(self.uri)
            print(f"Connected to {self.uri}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    async def receive_loop(self):
        """Listens for messages indefinitely."""
        try:
            while self.is_running:
                message = await self.connection.recv()
                if self.on_message_callback:
                    self.on_message_callback(message)
        except websockets.ConnectionClosed:
            print("Disconnected from server.")
            self.is_running = False
            if self.on_connection_lost_callback:
                self.on_connection_lost_callback()

    def on_message_received(self, message):
        """This is called by receive_loop when a message arrives."""
        print(f"Network Received: {message}")
        if self.on_message_callback:
            # Trigger the UI function
            self.on_message_callback(message)

    async def send_connect_message(self, username):
        """Sends the initial connection metadata."""
        import json
        if self.connection:
            try:
                await self.connection.send(json.dumps({
                    "action": "connect",
                    "username": username
                }))
            except websockets.ConnectionClosed:
                print("Connection lost.")

    async def send_message(self, username, message):
        """Sends a structured JSON message."""
        import json
        if self.connection:
            try:
                await self.connection.send(json.dumps({
                    "action": "message",
                    "username": username,
                    "content": message
                }))
            except websockets.ConnectionClosed:
                print("Connection lost.")
        else:
            print("Not connected to server.")

    async def close(self):
        """Closes the connection safely."""
        if self.connection:
            await self.connection.close()
            print("Client closed.")

# # --- How to use it ---
# async def run_example():
#     client = MyClient()
    
#     # Try to connect
#     if await client.connect():
#         # This starts the background loop
#         client.is_running = True
#         asyncio.create_task(client.receive_loop()) 
        
#         await client.send_message(username='mdrayhan03', message="Hello!")
        
#         print("Client is now staying alive to receive messages...")
#         await asyncio.Future()

# if __name__ == "__main__":
#     asyncio.run(run_example())