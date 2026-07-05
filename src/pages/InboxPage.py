import asyncio

from kivy.clock import Clock
from kivy.logger import Logger
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemLeadingIcon
from kivymd.uix.screen import MDScreen

from services.schemas import (
    ActiveUsersPacket,
    ChatMessagePacket,
    MediaItem,
    parse_packet,
)
from src.components.Header import Header
from src.components.MessageSend import MessageSend
from src.layouts.InboxLayout import InboxLayout


class InboxPageScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from kivymd.app import MDApp
        self.app = MDApp.get_running_app()

    def on_enter(self):
        """When user opens this screen, link the network listener to the UI."""
        if self.app.client:
            self.app.client.on_message_callback = self.process_incoming_msg

    def process_incoming_msg(self, message_text):
        """Triggered by the background task when a JSON message arrives."""
        packet = parse_packet(message_text)
        if packet is None:
            Logger.warning("Inbox: Dropping malformed packet")
            return

        # CRITICAL: Use Clock to move the data from background to Main UI Thread
        if isinstance(packet, ChatMessagePacket):
            Clock.schedule_once(lambda dt: self.add_message_to_ui(packet))
        elif isinstance(packet, ActiveUsersPacket):
            Clock.schedule_once(lambda dt: self.update_active_users(packet))

    def add_message_to_ui(self, packet):
        """Adds a validated chat message to the InboxLayout."""
        try:
            media_items = [item.model_dump() for item in packet.media_items]
            if packet.message or media_items:
                self.ids.inbox_list.add_message(
                    username=packet.username,
                    message=packet.message,
                    media_items=media_items,
                )
        except Exception as e:
            Logger.error(f"Inbox: UI update error: {e}")

    def update_active_users(self, packet):
        """Updates the sidebar with active users."""
        if 'active_users_menu' not in self.ids:
            Logger.error("Inbox: active_users_menu not found in ids!")
            return

        Logger.info(f"Inbox: Active users updated: {packet.users}")

        menu = self.ids.active_users_menu
        menu.clear_widgets()

        for user in packet.users:
            menu.add_widget(
                MDListItem(
                    MDListItemLeadingIcon(icon="account-circle"),
                    MDListItemHeadlineText(text=str(user)),
                )
            )

    def send_message_logic(self):
        """Handles sending messages from the UI."""
        input_bar = self.ids.message_input_bar
        input_field = input_bar.ids.text_input
        msg_text = input_field.text.strip()
        files = list(getattr(input_bar, 'selected_files', []))

        if not msg_text and not files:
            return

        username = self.app.user_data["username"]

        if not files:
            # 1. Update UI immediately for 'Self'
            self.ids.inbox_list.add_own_message(username=username, message=msg_text)

            # 2. Push to Network
            if self.app.client and self.app.client.connection:
                asyncio.create_task(self.app.client.send_message(username, msg_text))
        else:
            # We have files! Register each with the local file server and
            # send them ALL inside ONE message.
            import os
            from services.websocket.get_server_ip import get_lan_ip

            http_server = getattr(self.app, 'http_server', None)
            if http_server is None:
                Logger.error("Inbox: File server not running; cannot share files")
                return

            host_ip = get_lan_ip()
            media_items = []
            for file_path in files:
                token = http_server.register_file(file_path)
                media_items.append(MediaItem(
                    file_name=os.path.basename(file_path),
                    download_url=f"http://{host_ip}:8080/download/{token}",
                ))

            # Show in own UI (single message with multiple items)
            self.ids.inbox_list.add_own_message(
                username=username,
                message=msg_text,
                media_items=[item.model_dump() for item in media_items],
            )

            # Network send (single packet with all files)
            if self.app.client and self.app.client.connection:
                packet = ChatMessagePacket(
                    message_type="media",
                    username=username,
                    message=msg_text,
                    media_items=media_items,
                )
                asyncio.create_task(self.app.client.send_packet(packet))

            # Clear files from UI
            input_bar.selected_files = []
            input_bar.update_file_preview()

        # 3. Cleanup
        input_field.text = ""
