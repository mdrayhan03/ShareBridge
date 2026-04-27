from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty, ListProperty
from datetime import datetime
from src.components.Media import MediaWidget

class Message(MDBoxLayout) :
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
                
        if self.media_items and 'msg_content' in self.ids:
            from kivymd.uix.button import MDIconButton
            from kivymd.uix.boxlayout import MDBoxLayout
            
            btn_layout = MDBoxLayout(orientation='horizontal', adaptive_height=True)
            
            btn = MDIconButton(
                icon="download",
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                theme_bg_color="Custom",
                md_bg_color=(0.2, 0.2, 0.2, 0.5)
            )
            btn.bind(on_release=self.download_all)
            
            btn_layout.add_widget(MDBoxLayout()) # spacer
            btn_layout.add_widget(btn)
            btn_layout.add_widget(MDBoxLayout()) # spacer
            
            self.ids.msg_content.add_widget(btn_layout)

    def download_all(self, instance):
        import webbrowser
        for item in self.media_items:
            url = item.get("download_url", "")
            if url:
                print(f"Downloading {item.get('file_name')} from {url}")
                webbrowser.open(url)