from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.lang import Builder
import webbrowser

class MediaWidget(MDBoxLayout):
    file_name = StringProperty("unknown_file")
    download_url = StringProperty("")
    download_progress = NumericProperty(0)
    is_downloading = BooleanProperty(False)

    pass
