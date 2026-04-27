import asyncio
import websockets

from get_ip import get_local_ip_offline


async def handle_client(websocket):
    print(f"New connection from {websocket.remote_address}")
    try:
        async for message in websocket:
            print(f"Received: {message}")
            await websocket.send(f"Server received: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

async def main():
    local_ip = get_local_ip_offline()
    port = 8765
    
    print(f"--- WebSocket Server Starting ---")
    print(f"Local IP: {local_ip}")
    print(f"Port: {port}")
    print(f"Tell your client to connect to: ws://{local_ip}:{port}")
    
    # We bind to 0.0.0.0 to be 'visible' on the network
    async with websockets.serve(handle_client, "0.0.0.0", port):
        await asyncio.Future()  # This keeps the server running forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")