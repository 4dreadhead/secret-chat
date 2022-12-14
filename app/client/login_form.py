from PyQt6 import QtCore, QtWidgets
import threading
from .connection import run_client


class LoginForm(QtWidgets.QMainWindow, object):
    def __init__(self, parent_window):
        super().__init__()
        self.setupUi(self)
        self.retranslateUi(self)
        self.parent_window = parent_window

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("sss")
        MainWindow.resize(330, 314)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(60, 40, 211, 51))
        self.groupBox.setObjectName("groupBox")
        self.login_field = QtWidgets.QPlainTextEdit(self.groupBox)
        self.login_field.setGeometry(QtCore.QRect(0, 20, 211, 31))
        self.login_field.setObjectName("plainTextEdit")
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setGeometry(QtCore.QRect(60, 120, 211, 51))
        self.groupBox_2.setObjectName("groupBox_2")
        self.password_field = QtWidgets.QPlainTextEdit(self.groupBox_2)
        self.password_field.setGeometry(QtCore.QRect(0, 20, 211, 31))
        self.password_field.setObjectName("plainTextEdit_2")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(60, 220, 211, 31))
        self.pushButton.setObjectName("pushButton")
        MainWindow.setCentralWidget(self.centralwidget)

        self.pushButton.clicked.connect(self.login)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
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
            )
        )
        self.parent_window.connection_thread.start()
