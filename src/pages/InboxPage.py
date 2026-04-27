import asyncio
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock

from src.components.Header import Header
from src.layouts.InboxLayout import InboxLayout
from src.components.MessageSend import MessageSend

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
        """Triggered by the background thread when a JSON message arrives."""
        import json
        try:
            data = json.loads(message_text)
        except json.JSONDecodeError:
            return
            
        action = data.get("action")
        
        if action == "message" or action == "chat_message":
            # CRITICAL: Use Clock to move the data from background to Main UI Thread
            Clock.schedule_once(lambda dt: self.add_message_to_ui(data))
        elif action == "active_users":
            Clock.schedule_once(lambda dt: self.update_active_users(data))

    def add_message_to_ui(self, data):
        """Parses the message action and adds it to the InboxLayout."""
        try:
            user = data.get("username", "Unknown")
            # Backwards compatibility for 'content' vs new 'message' schema
            text = data.get("message", data.get("content", ""))
            
            is_media = (data.get("message_type") == "media")
            media_items = data.get("media_items", [])
            
            # Catch old formatting if it slips through
            if not media_items and data.get("file_name"):
                media_items = [{"file_name": data.get("file_name"), "download_url": data.get("download_url", "")}]
            
            if text or is_media:
                self.ids.inbox_list.add_message(
                    username=user, 
                    message=text,
                    media_items=media_items
                )
        except Exception as e:
            print(f"UI Update Error: {e}")

    def update_active_users(self, data):
        """Updates the sidebar with active users."""
        users = data.get("users", [])
        print(f"Active users updated: {users}")
        
        if 'active_users_menu' not in self.ids:
            print("ERROR: active_users_menu not found in ids!")
            return
            
        print(f"Updating menu. Found {len(users)} users.")
            
        menu = self.ids.active_users_menu
        menu.clear_widgets()
        
        from kivy.lang import Builder
        

        # 3. Add Users
        for user in users:
            safe_user = str(user).replace('"', '\\"')
            item_kv = f'''
MDListItem:
    MDListItemLeadingIcon:
        icon: "account-circle"
    MDListItemHeadlineText:
        text: "{safe_user}"
'''
            menu.add_widget(Builder.load_string(item_kv))
    def send_message_logic(self):
        """Handles sending messages from the UI."""
        import os
        import json
        import socket
        
        input_bar = self.ids.message_input_bar
        input_field = input_bar.ids.text_input
        msg_text = input_field.text.strip()
        files = list(getattr(input_bar, 'selected_files', []))
        
        if not msg_text and not files:
            return
            
        if msg_text and not files:
            # 1. Update UI immediately for 'Self'
            self.ids.inbox_list.add_own_message(
                username=self.app.user_data["username"], 
                message=msg_text
            )
            
            # 2. Push to Network
            if self.app.client and self.app.client.connection:
                asyncio.create_task(
                    self.app.client.send_message(
                        self.app.user_data["username"], 
                        msg_text
                    )
                )
        elif files:
            # We have files! Send them ALL inside ONE message
            media_items = []
            host_ip = ""
            try:
                host_ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                pass
                
            for file_path in files:
                file_name = os.path.basename(file_path)
                safe_path = file_path.replace('\\', '/')
                download_url = f"http://{host_ip}:8080/download/{safe_path}" if host_ip else ""
                
                media_items.append({
                    "file_name": file_name,
                    "download_url": download_url
                })
            
            # Show in own UI (single message with multiple items)
            self.ids.inbox_list.add_own_message(
                username=self.app.user_data["username"], 
                message=msg_text,
                media_items=media_items
            )
            
            # Network send (single packet with all files)
            if self.app.client and self.app.client.connection:
                packet = {
                    "action": "chat_message",
                    "message_type": "media",
                    "username": self.app.user_data["username"],
                    "message": msg_text,
                    "media_items": media_items
                }
                
                asyncio.create_task(
                    self.app.client.connection.send(json.dumps(packet))
                )
                    
            # Clear files from UI
            input_bar.selected_files = []
            input_bar.update_file_preview()
            
        # 3. Cleanup
        input_field.text = ""