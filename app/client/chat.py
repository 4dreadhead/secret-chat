from queue import Queue
import datetime
import uuid
from PyQt6 import QtCore, QtWidgets
from .login_form import LoginForm
from .models import User, Message
from app.crypto import SHA1


class Chat(QtWidgets.QMainWindow, object):
    TICK_INTERVAL = 250

    def __init__(self):
        super().__init__()
        self.online_users_list = []
        self.messages_list = []
        self.pending_messages_list = []
        self.current_user = None
        self.queue_in = Queue()
        self.queue_out = Queue()
        self.connection_thread = None
        self.online_users_list = []
        self.authorized = False
        self.me = None
        self.login_form = None
        self.timer = QtCore.QTimer()
        self.setup_ui()
        self.re_translate_ui()

    def closeEvent(self, event):
        self.queue_out.put({"method": "logout"})

        if self.connection_thread:
            self.connection_thread = None

        event.accept()

    def setup_ui(self):
        self.setObjectName("MainWindow")
        self.resize(1108, 570)
        self.setMaximumSize(1108, 570)
        self.setMinimumSize(760, 570)
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.new_message = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.new_message.setGeometry(QtCore.QRect(20, 450, 531, 101))
        self.new_message.setObjectName("textEdit")

        self.send_message = QtWidgets.QPushButton(self.centralwidget)
        self.send_message.setGeometry(QtCore.QRect(560, 450, 191, 51))
        self.send_message.setObjectName("pushButton")

        # self.select_file = QtWidgets.QPushButton(self.centralwidget)
        # self.select_file.setGeometry(QtCore.QRect(560, 510, 91, 41))
        # self.select_file.setObjectName("pushButton_2")

        self.get_hash = QtWidgets.QPushButton(self.centralwidget)
        self.get_hash.setGeometry(QtCore.QRect(560, 510, 191, 41))
        self.get_hash.setObjectName("pushButton_3")

        self.online_users = QtWidgets.QListWidget(self.centralwidget)
        self.online_users.setGeometry(QtCore.QRect(770, 60, 321, 251))
        self.online_users.setObjectName("listWidget")

        self.session_key = QtWidgets.QTextBrowser(self.centralwidget)
        self.session_key.setGeometry(QtCore.QRect(770, 330, 321, 101))
        self.session_key.setObjectName("plainTextEdit")

        self.hash = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.hash.setGeometry(QtCore.QRect(770, 450, 321, 101))
        self.hash.setObjectName("plainTextEdit_2")

        self.login = QtWidgets.QPushButton(self.centralwidget)
        self.login.setGeometry(QtCore.QRect(940, 10, 151, 31))
        self.login.setObjectName("pushButton_4")

        self.status = QtWidgets.QLabel(self.centralwidget)
        self.status.setGeometry(QtCore.QRect(770, 10, 151, 31))
        self.status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status.setObjectName("textBrowser")

        self.messages = QtWidgets.QListWidget(self.centralwidget)
        self.messages.setGeometry(QtCore.QRect(20, 10, 731, 421))
        self.messages.setObjectName("listWidget_2")

        self.setCentralWidget(self.centralwidget)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.login.clicked.connect(self.open_login_form)
        self.send_message.clicked.connect(self.send)
        self.get_hash.clicked.connect(self.calculate_hash)
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(self.TICK_INTERVAL)

    def set_online_user(self, user):
        item = QtWidgets.QListWidgetItem()
        item.username = user

        widget = QtWidgets.QWidget()
        widget_text = QtWidgets.QLabel(user.login)
        widget_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.addWidget(widget_text)
        widget_layout.addStretch()

        widget.setLayout(widget_layout)
        item.setSizeHint(widget.sizeHint())

        self.online_users.addItem(item)
        self.online_users.itemClicked.connect(self.select_user)
        self.online_users.setItemWidget(item, widget_text)

    def set_message(self, from_user, message, sent_at):
        item = QtWidgets.QListWidgetItem()
        item.username = from_user

        widget = QtWidgets.QWidget()
        widget_user = QtWidgets.QLabel(f"[ {from_user} ]  [ {sent_at} ]")
        widget_message = QtWidgets.QLabel(message)
        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.addWidget(widget_user, stretch=1)
        widget_layout.addWidget(widget_message)

        if from_user == self.me.login:
            widget_user.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            widget_message.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        else:
            widget_user.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            widget_message.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        widget_layout.addStretch()
        widget.setLayout(widget_layout)
        item.setSizeHint(widget.sizeHint())

        self.messages.addItem(item)
        self.messages.setItemWidget(item, widget)
        self.messages.scrollToBottom()

    def select_user(self, item):
        if not self.authorized:
            return
        if self.current_user == item.username:
            return
        self.switch_to_user(item.username)

    def switch_to_user(self, user):
        self.current_user = user
        self.messages.clear()
        for message in user.messages:
            self.set_message(message.from_user, message.text, message.sent_at)

        print(f"Switching to user {user.login}")

    def open_login_form(self):
        if self.authorized:
            self.online_users.clear()
            self.messages.clear()

            self.queue_out.put({"method": "logout"})

            if self.connection_thread:
                self.connection_thread = None

            self.status.setText("Вы не авторизованы")
            self.login.setText("Войти")

            self.current_user = None
            self.authorized = False

        else:
            self.login_form = LoginForm(self)
            self.login_form.show()

    def check_queue(self, max_tasks_per_iteration=3):
        if self.queue_in is None or self.queue_out is None:
            return

        for _ in range(max_tasks_per_iteration):
            if self.queue_in.empty():
                break

            payload = self.queue_in.get()
            self.handle_task(payload)
            self.queue_in.task_done()

        self.timer.start(self.TICK_INTERVAL)

    def send(self):
        if not self.authorized:
            return

        text = self.new_message.toPlainText()
        if not text:
            return

        current_hash = self.hash.toPlainText()
        if current_hash:
            sha1_hash = current_hash
        else:
            sha1_hash = SHA1(text).to_hash()

        message = Message(
            str(uuid.uuid4()),
            self.me.login,
            self.current_user.login,
            text,
            datetime.datetime.now().strftime("%d.%m.%y %H:%M"),
            sha1_hash
        )

        self.queue_out.put({
            "method": "send_message",
            "username": message.to_user,
            "message": message.text,
            "mid": message.mid,
            "sha1_hash": message.sha1_hash
        })
        self.pending_messages_list.append(message)
        self.new_message.clear()
        self.hash.clear()

    def handle_task(self, payload):
        match payload["method"]:
            case "userdata":
                self.set_user_data_to_session(payload)
            case "update_key":
                self.update_key(payload)
            case "close_connection":
                self.send_close_connection()
            case "user_joined":
                self.set_new_user(payload)
            case "user_left":
                self.remove_left_user(payload)
            case "new_message":
                self.set_new_message(payload)
            case "message_verification_failed":
                self.deny_message(payload)
            case "message_verification_pending":
                self.pending_message(payload)
            case "message_verification_done":
                self.accept_message(payload)

    def update_key(self, payload):
        des_key = bytearray([int(payload["session_key"][i:i + 8], 2) for i in range(0, len(payload["session_key"]), 8)])
        des_key_hex = "".join([format(i, 'x') for i in des_key])
        self.session_key.setPlainText(str(des_key_hex))

    def accept_message(self, payload):
        accepted_message = Message.find(self.pending_messages_list, payload["mid"])
        user = User.find(self.online_users_list, accepted_message.to_user)
        self.add_message_to_user(accepted_message, user)
        self.set_message(self.me.login, accepted_message.text, accepted_message.sent_at)
        self.pending_messages_list.remove(accepted_message)
        self.messages_list.append(accepted_message)

    def pending_message(self, payload):
        pending_message = Message.find(self.pending_messages_list, payload["old_mid"])
        pending_message.mid = payload["mid"]

    def deny_message(self, payload):
        pass

    def set_user_data_to_session(self, payload):
        self.online_users_list = list(map(User, payload["online_users"]))
        self.messages_list = list(map(lambda x: Message(*x), payload["messages"]))

        self.authorized = True
        self.me = User(payload["login"])
        self.login.setText("Выйти")
        self.status.setText(self.me.login)

        for user in self.online_users_list:
            self.set_online_user(user)
            for message in self.messages_list:
                self.add_message_to_user(message, user)
        self.current_user = self.online_users_list[0]

        for message in self.current_user.messages:
            self.set_message(message.from_user, message.text, message.sent_at)

        if self.login_form:
            self.login_form.close()
            self.login_form = None

    def calculate_hash(self):
        current_text = self.new_message.toPlainText()
        sha1_hash = SHA1(current_text).to_hash()

        self.hash.setPlainText(sha1_hash)

    def send_close_connection(self):
        self.online_users.clear()
        self.messages.clear()

        if self.login_form:
            self.login_form.close()
            self.login_form = None

            self.queue_out.put({"method": "logout"})

        if self.connection_thread:
            self.connection_thread = None

        self.authorized = False

    def set_new_user(self, payload):
        user = User(payload["username"])
        self.online_users_list.append(user)
        self.set_online_user(user)
        for message in self.messages_list:
            self.add_message_to_user(message, user)

    def remove_left_user(self, payload):
        user_to_remove = None

        for user in self.online_users_list:
            if payload["username"] == user.login:
                self.online_users_list.remove(user)
                user_to_remove = user

        for i in range(self.online_users.count()):
            if user_to_remove == self.online_users.item(i).username:
                self.online_users.takeItem(i)
                break

    def set_new_message(self, payload):
        print("new message")
        if payload["from_user"] == self.me.login:
            return

        new_message = Message(
            payload["mid"],
            payload["from_user"],
            self.me.login,
            payload["message"],
            payload["sent_at"],
            payload["sha1_hash"]
        )
        self.messages_list.append(new_message)
        for user in self.online_users_list:
            if user.login == payload["from_user"]:
                user.add_message(new_message)
                if self.current_user == user:
                    self.set_message(user.login, new_message.text, new_message.sent_at)

    def add_message_to_user(self, message, user):
        if message.from_user == self.me.login == user.login != message.to_user:
            return
        elif message.from_user == user.login and message.to_user != user.login:
            user.add_message(message)
        elif message.from_user == self.me.login and message.to_user == user.login and self.me.login != user.login:
            user.add_message(message)
        elif message.from_user == message.to_user == user.login:
            user.add_message(message)

    def re_translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "Чат"))
        self.send_message.setText(_translate("MainWindow", "Отправить"))
        # self.select_file.setText(_translate("MainWindow", "Файл"))
        self.get_hash.setText(_translate("MainWindow", "Хэш"))
        self.login.setText(_translate("MainWindow", "Войти"))
        self.status.setText("Вы не авторизованы")
