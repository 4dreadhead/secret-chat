import string
from PyQt6 import QtWidgets, QtCore


class InputWithAction(QtWidgets.QPlainTextEdit):
    def __init__(self, widget, submit_action, filter_as=None):
        super().__init__(widget)
        self.submit_action = submit_action
        match filter_as:
            case "login":
                self.filter = string.ascii_letters + string.digits
            case "password":
                self.filter = string.ascii_letters + string.digits + string.punctuation
            case _:
                self.filter = None

    def keyPressEvent(self, e):
        key_code = e.key()
        if key_code in [QtCore.Qt.Key.Key_Control, QtCore.Qt.Key.Key_Shift, QtCore.Qt.Key.Key_Alt,
                        QtCore.Qt.Key.Key_Meta, QtCore.Qt.Key.Key_Backspace, QtCore.Qt.Key.Key_Paste,
                        QtCore.Qt.Key.Key_Copy, QtCore.Qt.Key.Key_Select]:
            super().keyPressEvent(e)
        elif key_code == QtCore.Qt.Key.Key_Return.value and self.submit_action:
            self.submit_action()
        else:
            if self.filter is None:
                super().keyPressEvent(e)
            else:
                if e.text() in self.filter:
                    super().keyPressEvent(e)

    def insertPlainText(self, text):
        if self.filter is None:
            super().insertPlainText(text)
            return

        accepted_text = ""
        for char in text:
            if char in self.filter:
                accepted_text += char

        super().insertPlainText(accepted_text)
