import socket

def get_server_ip():
    port = 8765
    # Check if the server is running on THIS device
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', port)) == 0:
            return "127.0.0.1"
    
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)