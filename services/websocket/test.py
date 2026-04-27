# from server import MyServer
# from client import MyClient
# from start_service import check_server_alive

# server = None
# client = None

# if not check_server_alive() :
#     server = MyServer()
#     server.start_server_logic()

# client = MyClient()
# client.connect()
# client.send_message('mdrayhan03', 'Test message')

from get_server_ip import get_server_ip

print(get_server_ip())