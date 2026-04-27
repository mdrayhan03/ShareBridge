from kivymd.uix.screen import MDScreen
from src.components.SettingsSidebar import SettingsSidebar
from src.components.ProfileSettings import ProfileSettings

class SettingsPageScreen(MDScreen):
    def on_enter(self):
        # Automatically load the profile data when entering the screen
        self.ids.profile_settings.load_data()

    def show_profile_settings(self):
        # Clears the right panel and loads the ProfileSettings component
        self.ids.right_panel.clear_widgets()
        self.ids.right_panel.add_widget(self.ids.profile_settings)
