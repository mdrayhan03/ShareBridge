import asyncio
import threading
import os

# Configure Kivy logging BEFORE kivy is imported:
#   - KIVY_NO_FILELOG: stop Kivy writing its own many-files logs (the "log issues");
#     we keep a single log file ourselves (see services/app_logger.py).
#   - KIVY_LOG_LEVEL: quiet console — no debug frame spam.
os.environ.setdefault("KIVY_NO_FILELOG", "1")
os.environ.setdefault("KIVY_LOG_LEVEL", "info")

from kivy.logger import Logger

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

        # Set up our single downloadable log file (see Settings > Logs & Feedback).
        from services.app_logger import setup_file_logging
        self.log_file_path = setup_file_logging(self.user_data_dir)
        Logger.info(f"App: Logging to {self.log_file_path}")

        # Mobile specific tweaks
        Window.softinput_mode = "below_target"
        Window.bind(on_keyboard=self.on_keyboard)
        
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"

        from src.pages import JoinPage, InboxPage, OpeningPage, SettingsPage

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
        self.sm.add_widget(SettingsPage.SettingsPageScreen(name="SettingsPage"))

        return self.sm

    def on_stop(self):
        """Clean up when the app closes: kill download links and stop servers."""
        Logger.info("App: Stopping — clearing download links and stopping servers")

        # Make every download link dead immediately (synchronous, always runs),
        # then best-effort free the HTTP port.
        http_server = getattr(self, "http_server", None)
        if http_server:
            http_server.clear_links()
            try:
                asyncio.create_task(http_server.stop())
            except Exception:
                pass

        # Stop the WebSocket server (frees port 8765) if we were the host.
        server = getattr(self, "server", None)
        if server:
            try:
                server.stop_server_logic()
            except Exception as e:
                Logger.error(f"App: error stopping server: {e}")

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
        
        Logger.info("Network: Looking for existing server on the network...")
        # Since discover_server_ip blocks for 3 seconds, run it in a thread to keep UI smooth
        discovered_ip = await asyncio.to_thread(discover_server_ip, 3.0)
        
        if not discovered_ip:
            # Show Dialog on main thread
            Clock.schedule_once(lambda dt: self.prompt_start_server(
                "No Server Found", 
                "We couldn't find a host on this Wi-Fi.\nDo you want to start your own server?"
            ))
        else:
            Logger.info(f"Network: Found host! Connecting as client to {discovered_ip}...")
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
        Logger.info("Network: User clicked START SERVER. Initializing host...")
        self._host_startup_task = asyncio.create_task(self._async_start_host())

    async def _async_start_host(self):
        from kivy.utils import platform
        import asyncio
        
        Logger.info("Network: Starting a new host server...")
        
        if platform == 'android':
            try:
                from jnius import autoclass
                # The Java class name generated by buildozer: <domain>.<package>.Service<Servicename>
                service = autoclass('org.test.sharebridge.ServiceSharebridgeservice')
                mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
                argument = ''
                service.start(mActivity, argument)
                Logger.info("Network: Triggered Android foreground service!")
            except Exception as e:
                Logger.error(f"Network: Failed to start Android service: {e}")
                
            await asyncio.sleep(2) # Give Android time to spin up the python process
            
        else:
            from services.websocket.server import MyServer
            from services.websocket.udp_discovery import start_udp_broadcaster
            import threading

            self.server = MyServer()
            # Start WebSocket server in background
            threading.Thread(target=self.server.start_server_logic, daemon=True).start()
            # Start broadcasting so others can find us
            threading.Thread(target=start_udp_broadcaster, daemon=True).start()

            await asyncio.sleep(1) # Let server warm up
        
        # Connect client to our own server
        await self.connect_as_client("127.0.0.1")

    async def connect_as_client(self, ip):
        from services.websocket.client import MyClient

        # Every peer serves its own attached files, so any participant
        # (not just the host) can share media.
        if not getattr(self, "http_server", None):
            from services.http_server import FileTransferServer
            self.http_server = FileTransferServer()
            asyncio.create_task(self.http_server.start())

        self.client = MyClient(host=ip)
        self.client.on_connection_lost_callback = self.on_connection_lost
        
        # Link the UI to receive messages!
        inbox_screen = self.root.get_screen("InboxPage")
        self.client.on_message_callback = inbox_screen.process_incoming_msg
        
        if await self.client.connect():
            self.client.is_running = True

            # Identify ourselves to the server (username + full name)
            await self.client.send_connect_message(
                self.user_data.get("username", "Unknown"),
                self.user_data.get("fullname", ""),
            )

            # Start listening for messages in the background
            asyncio.create_task(self.client.receive_loop())

            # If we're the host we connect to ourselves via loopback, but show
            # the real LAN IP so the user can share it with others.
            is_host = ip in ("127.0.0.1", "localhost")
            if is_host:
                from services.websocket.get_server_ip import get_lan_ip
                display_ip = get_lan_ip()
            else:
                display_ip = ip

            # Show connected popup instead of directly going to inbox
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.show_connected_popup(display_ip, is_host))

    def wait_action(self):
        Logger.info("Network: User chose to wait. Will retry in 3 seconds.")
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: asyncio.create_task(self.retry_connection()), 3)

    async def retry_connection(self):
        from services.websocket.udp_discovery import discover_server_ip
        from kivy.clock import Clock
        
        Logger.info("Network: Retrying to find server...")
        discovered_ip = await asyncio.to_thread(discover_server_ip, 3.0)
        
        if discovered_ip:
            await self.connect_as_client(discovered_ip)
        else:
            Clock.schedule_once(lambda dt: self.prompt_start_server(
                "No Server Found", 
                "Still couldn't find a host on this Wi-Fi.\nDo you want to start your own server?"
            ))

    def show_connected_popup(self, ip, is_host=False):
        from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
        from kivymd.uix.button import MDButton, MDButtonText

        if is_host:
            headline = "Server Started"
            supporting = f"You are hosting.\nOthers on this Wi-Fi can join you at:\n{ip}"
        else:
            headline = "Connected!"
            supporting = f"Successfully connected to host at {ip}"

        btn_ok = MDButton(MDButtonText(text="OK"), style="text")

        self.connected_dialog = MDDialog(
            MDDialogHeadlineText(text=headline),
            MDDialogSupportingText(text=supporting),
            MDDialogButtonContainer(btn_ok)
        )
        
        def on_ok(instance):
            self.connected_dialog.dismiss()
            self.go_to_inbox()
            
        btn_ok.bind(on_release=on_ok)
        self.connected_dialog.open()

    def go_to_inbox(self):
        self.root.current = "InboxPage"

    async def check_for_updates(self):
        """Ask GitHub if a newer release exists; notify if so. Never disrupts the app."""
        from services.update_checker import check_for_update
        from version import __version__, GITHUB_OWNER, GITHUB_REPO

        info = await check_for_update(__version__, GITHUB_OWNER, GITHUB_REPO)
        if info:
            Logger.info(f"Update: {info['version']} available")
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.show_update_dialog(info))
        else:
            Logger.info("Update: running the latest version")

    def show_update_dialog(self, info):
        from kivymd.uix.dialog import (
            MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer,
        )
        from kivymd.uix.button import MDButton, MDButtonText
        from version import DOWNLOAD_PAGE_URL

        notes = info.get("notes", "")
        if len(notes) > 220:
            notes = notes[:220] + "…"
        text = f"Version {info['version']} is available."
        if notes:
            text += f"\n\n{notes}"

        btn_later = MDButton(MDButtonText(text="LATER"), style="text")
        btn_get = MDButton(MDButtonText(text="DOWNLOAD"), style="text")

        self.update_dialog = MDDialog(
            MDDialogHeadlineText(text="Update Available"),
            MDDialogSupportingText(text=text),
            MDDialogButtonContainer(btn_later, btn_get),
        )

        btn_later.bind(on_release=lambda *a: self.update_dialog.dismiss())

        def _download(*a):
            self.update_dialog.dismiss()
            self._open_url(DOWNLOAD_PAGE_URL)

        btn_get.bind(on_release=_download)
        self.update_dialog.open()

    def _open_url(self, url):
        from kivy.utils import platform
        if platform == "android":
            try:
                from jnius import autoclass
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                PythonActivity.mActivity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
            except Exception as e:
                Logger.error(f"Update: could not open {url}: {e}")
        else:
            import webbrowser
            try:
                webbrowser.open(url)
            except Exception as e:
                Logger.error(f"Update: could not open {url}: {e}")

    def on_connection_lost(self):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.prompt_start_server(
            "Connection Lost", 
            "The host server has disconnected.\nDo you want to start a new server?"
        ))



    def on_start(self):
        """Account check and triggering the network task."""
        Logger.info("App: Start!")
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

        # Quietly check for a newer release in the background (offline-safe).
        asyncio.create_task(self.check_for_updates())

if __name__ == "__main__":
    app = ShareBridgeApp()
    # This runs Kivy and Asyncio together
    try:
        asyncio.run(app.async_run(async_lib='asyncio'))
    except KeyboardInterrupt:
        pass