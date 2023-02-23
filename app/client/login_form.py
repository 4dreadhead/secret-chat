from PyQt6 import QtCore, QtWidgets
import threading
from .connection import run_client
from .widgets import InputWithAction


class LoginForm(QtWidgets.QMainWindow, object):
    def __init__(self, parent_window):
        super().__init__()
        self.setup_ui()
        self.re_translate_ui()
        self.parent_window = parent_window

    def setup_ui(self):
        self.setObjectName("LoginForm")
        self.resize(330, 314)
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(60, 40, 211, 51))
        self.groupBox.setObjectName("groupBox")
        self.login_field = InputWithAction(self.groupBox, None, filter_as="login")
        self.login_field.setGeometry(QtCore.QRect(0, 20, 211, 31))
        self.login_field.setObjectName("plainTextEdit")
        self.login_field.setTabChangesFocus(True)
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setGeometry(QtCore.QRect(60, 120, 211, 51))
        self.groupBox_2.setObjectName("groupBox_2")
        self.password_field = InputWithAction(self.groupBox_2, self.login, filter_as="password")
        self.password_field.setGeometry(QtCore.QRect(0, 20, 211, 31))
        self.password_field.setObjectName("plainTextEdit_2")
        self.password_field.setTabChangesFocus(True)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(60, 220, 211, 31))
        self.pushButton.setObjectName("pushButton")
        self.setCentralWidget(self.centralwidget)

        self.pushButton.clicked.connect(self.login)
        QtCore.QMetaObject.connectSlotsByName(self)

    def re_translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "Вход"))
        self.groupBox.setTitle(_translate("MainWindow", "Логин"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Пароль"))
        self.pushButton.setText(_translate("MainWindow", "Войти"))

    def login(self):
        self.parent_window.connection_thread = threading.Thread(
            target=lambda: run_client(
                self.login_field.toPlainText(),
                self.password_field.toPlainText(),
                queue_in=self.parent_window.queue_out,
                queue_out=self.parent_window.queue_in
            ),
            daemon=True
        )
        self.parent_window.connection_thread.start()
