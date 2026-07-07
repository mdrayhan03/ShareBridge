import socket


def get_lan_ip() -> str:
    """Return this machine's LAN IP (the interface used to reach the network).

    Uses the UDP-connect trick: no packet is actually sent, the OS just
    picks the outbound interface. Reliable where gethostbyname(gethostname())
    often returns 127.0.0.1.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.0)  # never block the UI thread waiting on this
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()
