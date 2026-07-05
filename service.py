import os
import sys
import threading
import asyncio
import logging
from time import sleep

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sharebridge.service")

# Ensure Kivy can find our local modules even in the service context
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from services.websocket.server import MyServer
from services.websocket.udp_discovery import start_udp_broadcaster

def run_servers():
    log.info("Starting ShareBridge backend service...")

    # 1. Start UDP Broadcaster
    threading.Thread(target=start_udp_broadcaster, daemon=True).start()

    # 2. Setup the loop for the WebSocket server.
    # The HTTP file server is NOT started here: it runs in the app process
    # on every peer, because the file token registry lives there.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    server = MyServer()

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
            log.info("Android WakeLock acquired successfully!")
    except Exception as e:
        log.info(f"Running outside Android or WakeLock failed: {e}")
        
    try:
        run_servers()
    finally:
        try:
            if 'wakelock' in locals() and wakelock.isHeld():
                wakelock.release()
                log.info("Android WakeLock released.")
        except Exception:
            pass
