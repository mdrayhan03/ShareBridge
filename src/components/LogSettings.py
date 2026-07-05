import os
import shutil
import urllib.parse
import webbrowser
from datetime import datetime

from kivy.core.clipboard import Clipboard
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

# Where feedback + logs should be sent.
FEEDBACK_EMAIL = "mostafaizurrahman2021@gmail.com"


class LogSettings(MDBoxLayout):
    contact_email = StringProperty(FEEDBACK_EMAIL)
    email_subject = StringProperty("")

    def refresh(self):
        """Recompute the display subject (called when the tab is opened)."""
        self.email_subject = self._subject()

    def copy_email(self):
        Clipboard.copy(self.contact_email)
        self._snack("Email address copied")

    def copy_subject(self):
        Clipboard.copy(self.email_subject or self._subject())
        self._snack("Subject copied")

    def _snack(self, message):
        MDSnackbar(
            MDSnackbarText(text=message),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
        ).open()

    def _log_path(self):
        app = MDApp.get_running_app()
        return getattr(app, "log_file_path", None)

    def _subject(self):
        app = MDApp.get_running_app()
        username = app.user_data.get("username", "unknown") if app else "unknown"
        date = datetime.now().strftime("%Y-%m-%d")
        # A structured subject so reports are easy to track and search.
        return f"ShareBridge Report | {username} | {date}"

    def export_log(self):
        """Copy the log file to a user-accessible Downloads folder."""
        log_path = self._log_path()
        if not log_path or not os.path.exists(log_path):
            self._snack("No log file found yet.")
            return

        # Ensure buffered records are flushed to disk before we copy.
        import logging
        for handler in logging.getLogger().handlers:
            try:
                handler.flush()
            except Exception:
                pass

        if platform == "android":
            try:
                from jnius import autoclass
                Environment = autoclass("android.os.Environment")
                base = Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DOWNLOADS
                ).getAbsolutePath()
                downloads_dir = os.path.join(base, "ShareBridge")
            except Exception as e:
                Logger.error(f"LogSettings: Android storage error: {e}")
                downloads_dir = "/storage/emulated/0/Download/ShareBridge"
        else:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads", "ShareBridge")

        try:
            os.makedirs(downloads_dir, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(downloads_dir, f"sharebridge_log_{stamp}.log")
            shutil.copyfile(log_path, dest)
            self._snack(f"Log exported to Downloads/ShareBridge")
            Logger.info(f"LogSettings: Log exported to {dest}")
        except Exception as e:
            Logger.error(f"LogSettings: Failed to export log: {e}")
            self._snack("Could not export log. See console.")

    def compose_email(self):
        """Open the mail client pre-filled with recipient, subject and body."""
        body = (
            "Hi,\n\n"
            "Here is my feedback / the issue I faced while using ShareBridge:\n\n"
            "1. What I was doing:\n"
            "2. What went wrong:\n"
            "3. What I expected:\n\n"
            "IMPORTANT: Please attach the log file you exported "
            "(Downloads/ShareBridge/sharebridge_log_*.log) before sending.\n\n"
            "Thanks!"
        )
        params = urllib.parse.urlencode(
            {"subject": self._subject(), "body": body}, quote_via=urllib.parse.quote
        )
        mailto = f"mailto:{FEEDBACK_EMAIL}?{params}"

        opened = False
        if platform == "android":
            try:
                from jnius import autoclass, cast
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                intent = Intent(Intent.ACTION_SENDTO)
                intent.setData(Uri.parse(mailto))
                activity = PythonActivity.mActivity
                activity.startActivity(intent)
                opened = True
            except Exception as e:
                Logger.error(f"LogSettings: Could not open mail intent: {e}")
        else:
            try:
                opened = webbrowser.open(mailto)
            except Exception as e:
                Logger.error(f"LogSettings: Could not open mail client: {e}")

        if not opened:
            self._snack(f"Email {FEEDBACK_EMAIL} with your log attached.")
