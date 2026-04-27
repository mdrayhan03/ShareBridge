from kivymd.uix.boxlayout import MDBoxLayout
from services.account_control import AccountControl

class ProfileSettings(MDBoxLayout):
    def load_data(self):
        ac = AccountControl()
        username, fullname = ac.read_account()
        self.ids.username_input.text = username if username else ""
        self.ids.fullname_input.text = fullname if fullname else ""

    def save_profile(self):
        username = self.ids.username_input.text.strip()
        fullname = self.ids.fullname_input.text.strip()
        
        if username and fullname:
            ac = AccountControl()
            ac.update_account(username, fullname)
            
            # Update app state
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            app.user_data["username"] = username
            app.user_data["fullname"] = fullname
            
            # Broadcast the updated username to the LAN server instantly
            if getattr(app, 'client', None) and app.client.is_running:
                import asyncio
                asyncio.create_task(app.client.send_connect_message(username))
            
            from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
            from kivy.metrics import dp
            MDSnackbar(
                MDSnackbarText(text="Profile updated successfully!"),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
            ).open()
