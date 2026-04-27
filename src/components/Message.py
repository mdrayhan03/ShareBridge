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
        if not hasattr(self, 'media_widgets'):
            self.media_widgets = {}
            
        for item in self.media_items:
            media_widget = MediaWidget(
                file_name=item.get("file_name", ""),
                download_url=item.get("download_url", "")
            )
            self.media_widgets[item.get("file_name", "")] = media_widget
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
            self.download_btn = btn
            btn.bind(on_release=self.download_all)
            
            btn_layout.add_widget(MDBoxLayout()) # spacer
            btn_layout.add_widget(btn)
            btn_layout.add_widget(MDBoxLayout()) # spacer
            
            self.ids.msg_content.add_widget(btn_layout)

    def download_all(self, instance):
        import asyncio
        asyncio.create_task(self.async_download_all())

    async def async_download_all(self):
        import aiohttp
        import os
        import asyncio
        from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
        from kivy.metrics import dp
        from kivy.clock import mainthread
        
        @mainthread
        def show_msg(msg):
            MDSnackbar(
                MDSnackbarText(text=msg),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
            ).open()
        
        loop = asyncio.get_running_loop()
        
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                Environment = autoclass('android.os.Environment')
                downloads_dir = os.path.join(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath(), "ShareBridge")
            except Exception as e:
                print(f"Android Storage Error: {e}")
                # Fallback if pyjnius fails for some reason
                downloads_dir = "/storage/emulated/0/Download/ShareBridge"
        else:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads", "ShareBridge")
            
        os.makedirs(downloads_dir, exist_ok=True)
        
        show_msg(f"Starting download of {len(self.media_items)} file(s)...")
        
        try:
            async with aiohttp.ClientSession() as session:
                for item in self.media_items:
                    url = item.get("download_url", "")
                    file_name = item.get("file_name", "unknown_file")
                    if url:
                        save_path = os.path.join(downloads_dir, file_name)
                        print(f"Downloading {file_name} to {save_path}...")
                        
                        async with session.get(url) as response:
                            response.raise_for_status()
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded = 0
                            
                            media_widget = getattr(self, 'media_widgets', {}).get(file_name)
                            if media_widget:
                                media_widget.is_downloading = True
                                media_widget.download_progress = 0
                                
                            with open(save_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(1024 * 1024 * 2): # 2MB chunks
                                    await loop.run_in_executor(None, f.write, chunk)
                                    downloaded += len(chunk)
                                    if total_size and media_widget:
                                        media_widget.download_progress = (downloaded / total_size) * 100
                                        
                            if media_widget:
                                media_widget.is_downloading = False
                                media_widget.download_progress = 100
                                    
            show_msg("Download complete! Saved in Downloads/ShareBridge")
            print(f"Download complete! Saved in {downloads_dir}")
            
            # Update the button to show a success tick
            if hasattr(self, 'download_btn'):
                self.download_btn.icon = "check-circle"
                self.download_btn.disabled = True
                
        except Exception as e:
            print(f"Download Error: {e}")
            show_msg("Download failed! Check console.")