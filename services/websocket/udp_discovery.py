import logging
import socket
import time

log = logging.getLogger(__name__)

BROADCAST_PORT = 37020
SERVER_PORT = 8765
BEACON_MESSAGE = b"SHAREBRIDGE_SERVER_HERE"


def _local_server_running(timeout=0.3):
    """Quick TCP probe: is a ShareBridge server already listening on this machine?"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex(("127.0.0.1", SERVER_PORT)) == 0


def start_udp_broadcaster():
    """Runs continuously in the background, broadcasting the server's existence."""
    # Set up UDP socket for broadcasting
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    log.info("[UDP] Started UDP Broadcaster...")
    broadcast_warned = False
    while True:
        # LAN beacon. On macOS this needs the 'Local Network' permission
        # (System Settings > Privacy & Security > Local Network) — warn once
        # instead of spamming if it's blocked.
        try:
            broadcaster.sendto(BEACON_MESSAGE, ('<broadcast>', BROADCAST_PORT))
            broadcast_warned = False
        except OSError as e:
            if not broadcast_warned:
                log.error(
                    f"[UDP] LAN broadcast failed ({e}). On macOS, allow 'Local Network' "
                    "access for your terminal in System Settings > Privacy & Security."
                )
                broadcast_warned = True

        # Loopback beacon so other instances on THIS machine always find us,
        # even when the LAN broadcast is blocked by OS permissions.
        try:
            broadcaster.sendto(BEACON_MESSAGE, ('127.0.0.1', BROADCAST_PORT))
        except OSError:
            pass

        time.sleep(2)  # Wait 2 seconds before shouting again


def discover_server_ip(timeout=3.0):
    """
    Finds an existing server: first checks this machine directly, then
    listens for UDP beacons from the network.
    Returns the IP string if found, or None if no server exists.
    """
    # A server on this same device is reachable without any UDP at all.
    if _local_server_running():
        log.info("[UDP] Found server running on this machine (127.0.0.1)")
        return "127.0.0.1"

    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Allow multiple apps to use this port (useful if testing on the same PC).
    # macOS needs SO_REUSEPORT for two listeners to share a UDP port.
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass

    # Bind to the broadcast port to listen
    listener.bind(("", BROADCAST_PORT))

    # Only wait for 'timeout' seconds. Don't freeze the app forever!
    listener.settimeout(timeout)

    log.info("[UDP] Searching local network for ShareBridge server...")
    try:
        while True:
            # Receive the message and the address it came from
            data, addr = listener.recvfrom(1024)

            if data == BEACON_MESSAGE:
                server_ip = addr[0]  # addr[0] is the IP address
                log.info(f"[UDP] Found server running at {server_ip}!")
                return server_ip

    except socket.timeout:
        log.info("[UDP] No existing server found.")
        return None
    finally:
        listener.close()
