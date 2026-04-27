import asyncio
import websockets
from get_ip import get_local_ip_offline
from start_server import main

async def connect_to_server():
    # REPLACE THIS with the IP printed by the server script
    server_ip = get_local_ip_offline()
    uri = f"ws://{server_ip}:8765"
    
    try:
        # Try to connect with a 2-second timeout
        async with asyncio.wait_for(websockets.connect(uri), timeout=2.0) as websocket:
            print("✅ Server is ONLINE and reachable!")
            await websocket.send("Status check: Are you there?")
            response = await websocket.recv()
            print(f"Server replied: {response}")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        main()
    
    return False

asyncio.run(connect_to_server())