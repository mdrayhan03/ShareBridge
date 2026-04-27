from kivymd.uix.boxlayout import MDBoxLayout
from kivy.core.window import Window
from plyer import filechooser
from kivy.clock import mainthread
from kivy.properties import ListProperty
import os
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton

class MessageSend(MDBoxLayout):
    selected_files = ListProperty([])

    def __init__(self, **kwargs):
        self.register_event_type('on_send')
        self.register_event_type('on_attachments')
        super().__init__(**kwargs)
        Window.bind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 40 and self.ids.text_input.focus:
            if 'shift' in modifiers:
                return False
            else:
                self.dispatch('on_send')
                return True
        return False

    def on_send(self, *args):
        pass

    def on_attachments(self, file_paths):
        pass

    def open_file_chooser(self):
        try:
            filechooser.open_file(multiple=True, on_selection=self._on_file_selection)
        except Exception as e:
            print(f"Error opening file chooser: {e}")

    @mainthread
    def _on_file_selection(self, selection):
        if selection:
            for file_path in selection:
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
            self.update_file_preview()
            self.dispatch('on_attachments', selection)

    def update_file_preview(self):
        preview_box = self.ids.files_preview_box
        files_container = self.ids.files_container
        files_container.clear_widgets()
        
        if not self.selected_files:
            preview_box.height = "0dp"
            preview_box.opacity = 0
            return
            
        preview_box.opacity = 1
        preview_box.height = "50dp"
        
        for file_path in self.selected_files:
            file_name = os.path.basename(file_path)
            
            card = MDCard(
                orientation="horizontal",
                size_hint_y=None,
                height="40dp",
                size_hint_x=None,
                width="180dp",
                padding="10dp",
                spacing="5dp",
                md_bg_color=(0.2, 0.2, 0.2, 1),
                radius=[8, 8, 8, 8]
            )
            
            lbl = MDLabel(text=file_name, theme_text_color="Custom", text_color=(1, 1, 1, 1), shorten=True, shorten_from="right")
            btn = MDIconButton(icon="close-circle", pos_hint={"center_y": 0.5}, theme_text_color="Custom", text_color=(1, 0, 0, 1))
            btn.bind(on_release=lambda x, p=file_path: self.remove_file(p))
            
            card.add_widget(lbl)
            card.add_widget(btn)
            files_container.add_widget(card)

    def remove_file(self, file_path):
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            self.update_file_preview()