from kivymd.uix.screen import MDScreen
from src.components.SettingsSidebar import SettingsSidebar
from src.components.ProfileSettings import ProfileSettings
from src.components.LogSettings import LogSettings
from src.components.AboutUs import AboutUs

class SettingsPageScreen(MDScreen):
    def on_enter(self):
        # Automatically load the profile data when entering the screen
        self.ids.profile_settings.load_data()
        self.show_profile_settings()

    def show_profile_settings(self):
        # Clears the right panel and loads the ProfileSettings component
        self.ids.right_panel.clear_widgets()
        self.ids.right_panel.add_widget(self.ids.profile_settings)

    def show_log_settings(self):
        # Clears the right panel and loads the LogSettings component
        self.ids.right_panel.clear_widgets()
        self.ids.log_settings.refresh()
        self.ids.right_panel.add_widget(self.ids.log_settings)

    def show_about_us(self):
        # Clears the right panel and loads the AboutUs component
        self.ids.right_panel.clear_widgets()
        self.ids.right_panel.add_widget(self.ids.about_us)
