from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText

class ServerActionDialog:
    def __init__(self, app, title, text, on_start, on_wait):
        self.app = app
        self.on_start = on_start
        self.on_wait = on_wait
        
        # Creating the buttons
        btn_wait = MDButton(
            MDButtonText(text="WAIT"),
            style="text",
            on_release=self._handle_wait
        )
        
        btn_start = MDButton(
            MDButtonText(text="START SERVER"),
            style="text",
            on_release=self._handle_start
        )
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=text),
            MDDialogButtonContainer(
                btn_wait,
                btn_start
            )
        )
        
    def _handle_wait(self, instance):
        print("User clicked WAIT.")
        self.dialog.dismiss()
        if self.on_wait:
            self.on_wait()
            
    def _handle_start(self, instance):
        print("User clicked START SERVER.")
        self.dialog.dismiss()
        if self.on_start:
            self.on_start()
            
    def open(self):
        self.dialog.open()
