from PyQt6 import QtWidgets
from app.client.qtapp.chat import Chat


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = Chat()
    ui.show()
    sys.exit(app.exec())
