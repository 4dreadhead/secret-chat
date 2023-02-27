import string
from PyQt6 import QtWidgets, QtCore, QtGui


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


class SideGrip(QtWidgets.QWidget):
    def __init__(self, parent, edge, grip_size):
        QtWidgets.QWidget.__init__(self, parent)
        self.grip_size = grip_size
        if edge == QtCore.Qt.Edge.LeftEdge:
            self.setCursor(QtCore.Qt.CursorShape.SizeHorCursor)
            self.resizeFunc = self.resizeLeft
        elif edge == QtCore.Qt.Edge.TopEdge:
            self.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
            self.resizeFunc = self.resizeTop
        elif edge == QtCore.Qt.Edge.RightEdge:
            self.setCursor(QtCore.Qt.CursorShape.SizeHorCursor)
            self.resizeFunc = self.resizeRight
        else:
            self.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
            self.resizeFunc = self.resizeBottom
        self.mousePos = None

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen(QtGui.QColor("#21252b"), 2 * self.grip_size)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width(), self.height())

    def resizeLeft(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() - delta.x())
        geo = window.geometry()
        geo.setLeft(geo.right() - width)
        window.setGeometry(geo)

    def resizeTop(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() - delta.y())
        geo = window.geometry()
        geo.setTop(geo.bottom() - height)
        window.setGeometry(geo)

    def resizeRight(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() + delta.x())
        window.resize(width, window.height())

    def resizeBottom(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() + delta.y())
        window.resize(window.width(), height)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.mousePos = event.pos()

    def mouseMoveEvent(self, event):
        if self.mousePos is not None:
            delta = event.pos() - self.mousePos
            self.resizeFunc(delta)

    def mouseReleaseEvent(self, event):
        self.mousePos = None

