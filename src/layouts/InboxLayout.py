from kivymd.uix.scrollview import MDScrollView

from src.components import Message, OwnMessage

class InboxLayout(MDScrollView) :
    def add_message(self, username, message, **kwargs):
        container = self.ids.message_queue
        new_msg = Message.Message(username=username, message=message, **kwargs)
        container.add_widget(new_msg)

    def add_own_message(self, username, message, **kwargs):
        container = self.ids.message_queue
        new_msg = OwnMessage.OwnMessage(username=username, message=message, **kwargs)
        container.add_widget(new_msg)