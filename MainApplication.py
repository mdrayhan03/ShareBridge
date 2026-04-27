import asyncio
import threading
import os

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivy.uix.screenmanager import SlideTransition
from kivy.lang import Builder
from kivy.properties import DictProperty

# Import your network logic
from services.websocket.server import MyServer
from services.websocket.client import MyClient

class ShareBridgeApp(MDApp):
    user_data = DictProperty({"username": "", "fullname": ""})
    
    # These will be accessible globally via MDApp.get_running_app().client
    server = None
    client = None

    def build(self):
        from kivy.core.window import Window
        
        # Mobile specific tweaks
        Window.softinput_mode = "below_target"
        Window.bind(on_keyboard=self.on_keyboard)
        
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"

        from src.pages import JoinPage, InboxPage, OpeningPage

        base_path = os.path.dirname(__file__)
        folders = [
            os.path.join(base_path, 'src/components'),
            os.path.join(base_path, 'src/layouts'),
            os.path.join(base_path, 'src/pages'),
        ]

        for folder in folders:
            for file in os.listdir(folder):
                if file.endswith('.kv'):
                    Builder.load_file(os.path.join(folder, file))

        self.sm = MDScreenManager(transition=SlideTransition(direction="left", duration=0.5))
        self.sm.add_widget(JoinPage.JoinPageScreen(name='JoinPage'))
        self.sm.add_widget(OpeningPage.OpeningPageScreen(name='OpeningPage'))
        self.sm.add_widget(InboxPage.InboxPageScreen(name="InboxPage"))

        return self.sm

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # 27 is the escape key / Android physical back button
            if self.sm.current == "InboxPage":
                # Prompt user or minimize? For now, let it exit or maybe disconnect safely
                if self.client:
                    # Clean up logic can go here
                    pass
                # Returning False allows Kivy to process the exit
                return False
            elif self.sm.current == "JoinPage" or self.sm.current == "OpeningPage":
                return False
        return False

    async def start_network_logic(self):
        """Prepares the networking without freezing the UI."""
        from services.websocket.udp_discovery import discover_server_ip
        from kivy.clock import Clock
        
        print("Looking for existing server on the network...")
        # Since discover_server_ip blocks for 3 seconds, run it in a thread to keep UI smooth
        discovered_ip = await asyncio.to_thread(discover_server_ip, 3.0)
        
        if not discovered_ip:
            # Show Dialog on main thread
            Clock.schedule_once(lambda dt: self.prompt_start_server(
                "No Server Found", 
                "We couldn't find a host on this Wi-Fi.\nDo you want to start your own server?"
            ))
        else:
            print(f"Found Host! Connecting as client to {discovered_ip}...")
            await self.connect_as_client(discovered_ip)

    def prompt_start_server(self, title, text):
        from src.components.ServerDialog import ServerActionDialog
        # Save a reference to prevent the dialog object from being garbage-collected
        self.active_dialog = ServerActionDialog(
            app=self,
            title=title,
            text=text,
            on_start=self.start_host_server_action,
            on_wait=self.wait_action
        )
        self.active_dialog.open()

    def start_host_server_action(self):
        # Save a reference to the task so the garbage collector doesn't destroy it mid-execution
        print("User clicked START SERVER. Initializing host...")
        self._host_startup_task = asyncio.create_task(self._async_start_host())

    async def _async_start_host(self):
        from services.websocket.server import MyServer
        from services.websocket.udp_discovery import start_udp_broadcaster
        from services.http_server import FileTransferServer
        import threading
        
        print("Starting a new Host Server...")
        self.server = MyServer()
        # Start WebSocket server in background
        threading.Thread(target=self.server.start_server_logic, daemon=True).start()
        # Start broadcasting so others can find us
        threading.Thread(target=start_udp_broadcaster, daemon=True).start()
        
        # Start the HTTP File Server for sharing media
        self.http_server = FileTransferServer()
        asyncio.create_task(self.http_server.start())
        
        await asyncio.sleep(1) # Let server warm up
        
        # Connect client to our own server
        await self.connect_as_client("127.0.0.1")

    async def connect_as_client(self, ip):
        from services.websocket.client import MyClient
        self.client = MyClient(host=ip)
        self.client.on_connection_lost_callback = self.on_connection_lost
        
        # Link the UI to receive messages!
        inbox_screen = self.root.get_screen("InboxPage")
        self.client.on_message_callback = inbox_screen.process_incoming_msg
        
        if await self.client.connect():
            self.client.is_running = True
            
            # Identify ourselves to the server
            await self.client.send_connect_message(self.user_data.get("username", "Unknown"))
            
            # Start listening for messages in the background
            asyncio.create_task(self.client.receive_loop())
            
            # Show connected popup instead of directly going to inbox
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.show_connected_popup(ip))

    def wait_action(self):
        print("User chose to wait. Will retry in 3 seconds.")
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: asyncio.create_task(self.retry_connection()), 3)

    async def retry_connection(self):
        from services.websocket.udp_discovery import discover_server_ip
        from kivy.clock import Clock
        
        print("Retrying to find server...")
        discovered_ip = await asyncio.to_thread(discover_server_ip, 3.0)
        
        if discovered_ip:
            await self.connect_as_client(discovered_ip)
        else:
            Clock.schedule_once(lambda dt: self.prompt_start_server(
                "No Server Found", 
                "Still couldn't find a host on this Wi-Fi.\nDo you want to start your own server?"
            ))

    def show_connected_popup(self, ip):
        from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
        from kivymd.uix.button import MDButton, MDButtonText
        
        btn_ok = MDButton(MDButtonText(text="OK"), style="text")
        
        self.connected_dialog = MDDialog(
            MDDialogHeadlineText(text="Connected!"),
            MDDialogSupportingText(text=f"Successfully connected to host at {ip}"),
            MDDialogButtonContainer(btn_ok)
        )
        
        def on_ok(instance):
            self.connected_dialog.dismiss()
            self.go_to_inbox()
            
        btn_ok.bind(on_release=on_ok)
        self.connected_dialog.open()

    def go_to_inbox(self):
        self.root.current = "InboxPage"

    def on_connection_lost(self):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.prompt_start_server(
            "Connection Lost", 
            "The host server has disconnected.\nDo you want to start a new server?"
        ))

    def on_start(self):
        """Account check and triggering the network task."""
        print("App start!")
        from services.account_control import AccountControl
        ac = AccountControl()
        username, fullname = ac.read_account()

        if username and fullname:
            self.user_data["username"] = username
            self.user_data["fullname"] = fullname
            self.root.transition.duration = 0
            self.root.current = "OpeningPage"
            self.root.transition.duration = 0.5

        # Launch network logic into the asyncio loop
        asyncio.create_task(self.start_network_logic())

if __name__ == "__main__":
    app = ShareBridgeApp()
    # This runs Kivy and Asyncio together
    try:
        asyncio.run(app.async_run(async_lib='asyncio'))
    except KeyboardInterrupt:
        pass