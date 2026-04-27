import asyncio
import websockets
import threading

from .get_server_ip import get_server_ip
from .server import MyServer
from .client import MyClient

async def check_server_alive() :
    ip = get_server_ip()
    uri = f"ws://{ip}:8765"

    try:
        connection = await asyncio.wait_for(websockets.connect(uri), timeout=2.0)
        async with connection as websocket:
            print("Server is ONLINE and reachable!")
            await websocket.send("Status check: Are you there?")
            response = await websocket.recv()
            print(f"Server replied: {response}")
            return True
        
    except asyncio.TimeoutError:
        print("Error: Connection timed out. Is the server running?")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

async def start() :
    connection = await check_server_alive()

    if not connection :
        server = MyServer()
        server_thread = threading.Thread(target=server.start_server_logic, daemon=True)
        server_thread.start()
    
    client = MyClient()
    client.connect()
    