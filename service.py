import os
import sys
import threading
import asyncio
from time import sleep

# Ensure Kivy can find our local modules even in the service context
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from services.websocket.server import MyServer
from services.websocket.udp_discovery import start_udp_broadcaster
from services.http_server import FileTransferServer

def run_servers():
    print("[Service] Starting ShareBridge Backend Service...")
    
    # 1. Start UDP Broadcaster
    threading.Thread(target=start_udp_broadcaster, daemon=True).start()
    
    # 2. Setup the loop for HTTP and WS
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    server = MyServer()
    http_server = FileTransferServer()
    
    # Start HTTP File Streamer
    loop.create_task(http_server.start())
    # Block and run WebSocket Signaling
    loop.run_until_complete(server.main_serve())

if __name__ == '__main__':
    # Add a safety delay for Android to initialize the process
    sleep(1)
    
    # Try to grab an Android WakeLock if running on a phone
    try:
        from jnius import autoclass
        Context = autoclass('android.content.Context')
        PythonService = autoclass('org.kivy.android.PythonService')
        
        service = PythonService.mService
        if service:
            pm = service.getSystemService(Context.POWER_SERVICE)
            # PARTIAL_WAKE_LOCK = 1
            wakelock = pm.newWakeLock(1, "ShareBridge::TransferWakeLock")
            wakelock.acquire()
            print("[Service] Android WakeLock Acquired successfully!")
    except Exception as e:
        print(f"[Service] Running outside Android or WakeLock failed: {e}")
        
    try:
        run_servers()
    finally:
        try:
            if 'wakelock' in locals() and wakelock.isHeld():
                wakelock.release()
                print("[Service] Android WakeLock Released.")
        except Exception:
            pass
