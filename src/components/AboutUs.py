import webbrowser

from kivy.logger import Logger
from kivy.properties import StringProperty
from kivy.utils import platform
from kivymd.uix.boxlayout import MDBoxLayout

from version import __version__

# Developer / project links.
DEVELOPER_NAME = "MD Rayhan Hossain"
DEVELOPER_TAGLINE = "Developer of ShareBridge"
LINKS = {
    "github": "https://github.com/mdrayhan03",
    "linkedin": "https://www.linkedin.com/in/mdrayhan03/",
    "portfolio": "https://rayhan-portfolio.lovable.app/",
}


class AboutUs(MDBoxLayout):
    app_version = StringProperty(__version__)

    def open_link(self, key):
        url = LINKS.get(key)
        if not url:
            return
        if platform == "android":
            try:
                from jnius import autoclass
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                PythonActivity.mActivity.startActivity(intent)
            except Exception as e:
                Logger.error(f"AboutUs: Could not open link {url}: {e}")
        else:
            try:
                webbrowser.open(url)
            except Exception as e:
                Logger.error(f"AboutUs: Could not open link {url}: {e}")
