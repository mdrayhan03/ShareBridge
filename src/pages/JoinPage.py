from kivymd.uix.screen import MDScreen

from src.components import Join
from services.account_control import AccountControl

class JoinPageScreen(MDScreen) :
    def process_join(self):
        username = self.ids.join_box.ids.user_field.text
        fullname = self.ids.join_box.ids.full_name_field.text
        
        if username and fullname:
            ac = AccountControl()
            ac.write_account(username, fullname)
            
            # Switch screen
            self.manager.current = "InboxPage"