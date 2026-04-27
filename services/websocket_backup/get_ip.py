import socket

def get_local_ip_offline():
    # Gets the hostname of your machine
    hostname = socket.gethostname()
    # Returns the IP address associated with that hostname
    try:
        return socket.gethostbyname(hostname)
    except:
        return "127.0.0.1"

# print(f"Use this IP for your WebSocket: {get_local_ip_offline()}")