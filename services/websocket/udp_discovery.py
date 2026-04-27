import socket
import time
import threading

def start_udp_broadcaster():
    """Runs continuously in the background, broadcasting the server's existence."""
    # Set up UDP socket for broadcasting
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    broadcast_port = 37020
    message = b"SHAREBRIDGE_SERVER_HERE"
    
    print("[UDP] Started UDP Broadcaster...")
    while True:
        try:
            # '<broadcast>' automatically targets all devices on the local Wi-Fi
            broadcaster.sendto(message, ('<broadcast>', broadcast_port))
            time.sleep(2)  # Wait 2 seconds before shouting again
        except Exception as e:
            print(f"Broadcast error: {e}")
            time.sleep(2)

def discover_server_ip(timeout=3.0):
    """
    Listens to the network to find an existing server.
    Returns the IP string if found, or None if no server exists.
    """
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    # Allow multiple apps to use this port (useful if testing on the same PC)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to the broadcast port to listen
    broadcast_port = 37020
    listener.bind(("", broadcast_port))
    
    # Only wait for 'timeout' seconds. Don't freeze the app forever!
    listener.settimeout(timeout)
    
    print(f"[UDP] Searching local network for ShareBridge server...")
    try:
        while True:
            # Receive the message and the address it came from
            data, addr = listener.recvfrom(1024)
            
            if data == b"SHAREBRIDGE_SERVER_HERE":
                server_ip = addr[0] # addr[0] is the IP address
                print(f"[UDP] Found server running at {server_ip}!")
                return server_ip
                
    except socket.timeout:
        print("[UDP] No existing server found.")
        return None
    finally:
        listener.close()
