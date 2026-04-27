from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty, ListProperty
from datetime import datetime
from src.components.Media import MediaWidget

class OwnMessage(MDBoxLayout) :
    username = StringProperty("default_user")
    message = StringProperty("Default Message")
    timestamp = StringProperty(datetime.now().strftime("%H:%M-%d/%m/%Y"))
    
    media_items = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = datetime.now().strftime("%H:%M-%d/%m/%Y")

    def on_kv_post(self, base_widget):
        for item in self.media_items:
            media_widget = MediaWidget(
                file_name=item.get("file_name", ""),
                download_url=item.get("download_url", "")
            )
            if 'msg_content' in self.ids:
                self.ids.msg_content.add_widget(media_widget)