from queue import Queue
import datetime
import uuid
from PyQt6 import QtCore, QtWidgets, QtGui
from app.client.qtapp.login_form import LoginForm
from app.client.models import User, Message
from app.client.qtapp.styles import *
from app.client.qtapp.ui import UiMainWindow
from app.crypto import SHA1
from app.client.qtapp.widgets import SideGrip


class Chat(QtWidgets.QMainWindow, UiMainWindow, object):
    TICK_INTERVAL = 150
    GRIP_SIZE = 1

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
        self.current_item = None
        self.me = None
        self.login_form = None
        self.timer = QtCore.QTimer()
        self.setupUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.online_users.setStyleSheet(LIST_AREA)
        self.messages.setStyleSheet(LIST_AREA)
        self.menu.clicked.connect(self.toggle_menu)
        self.login.clicked.connect(self.open_login_form)
        self.send_button.clicked.connect(self.send)
        self.get_hash.clicked.connect(self.calculate_hash)
        self.close_button.clicked.connect(self.close)
        self.minimize.clicked.connect(self.showMinimized)
        self.maximize.clicked.connect(self.toggle_maximized)
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(self.TICK_INTERVAL)
        self.old_pos = None

        self.sideGrips = [
            SideGrip(self, QtCore.Qt.Edge.LeftEdge),
            SideGrip(self, QtCore.Qt.Edge.TopEdge),
            SideGrip(self, QtCore.Qt.Edge.RightEdge),
            SideGrip(self, QtCore.Qt.Edge.BottomEdge),
        ]
        self.cornerGrips = [QtWidgets.QSizeGrip(self) for _ in range(4)]
        for grip in self.cornerGrips:
            grip.setStyleSheet("color: #21252b; background-color: #21252b;")

    def setGripSize(self, size):
        if size == self.GRIP_SIZE:
            return
        self.updateGrips()

    def updateGrips(self):
        self.setContentsMargins(*[self.GRIP_SIZE] * 4)

        outRect = self.rect()
        # an "inner" rect used for reference to set the geometries of size grips
        inRect = outRect.adjusted(self.GRIP_SIZE, self.GRIP_SIZE,
                                  -self.GRIP_SIZE, -self.GRIP_SIZE)

        # top left
        self.cornerGrips[0].setGeometry(
            QtCore.QRect(outRect.topLeft(), inRect.topLeft()))
        # top right
        self.cornerGrips[1].setGeometry(
            QtCore.QRect(outRect.topRight(), inRect.topRight()).normalized())
        # bottom right
        self.cornerGrips[2].setGeometry(
            QtCore.QRect(inRect.bottomRight(), outRect.bottomRight()))
        # bottom left
        self.cornerGrips[3].setGeometry(
            QtCore.QRect(outRect.bottomLeft(), inRect.bottomLeft()).normalized())

        # left edge
        self.sideGrips[0].setGeometry(
            0, inRect.top(), self.GRIP_SIZE, inRect.height())
        # top edge
        self.sideGrips[1].setGeometry(
            inRect.left(), 0, inRect.width(), self.GRIP_SIZE)
        # right edge
        self.sideGrips[2].setGeometry(
            inRect.left() + inRect.width(),
            inRect.top(), self.GRIP_SIZE, inRect.height())
        # bottom edge
        self.sideGrips[3].setGeometry(
            self.GRIP_SIZE, inRect.top() + inRect.height(),
            inRect.width(), self.GRIP_SIZE)

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.updateGrips()

    def toggle_menu(self):
        if self.side_contents.isHidden():
            self.side_contents.show()
        else:
            self.side_contents.hide()

    def toggle_maximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def show_menu(self):
        self.side_contents.setMinimumSize(QtCore.QSize(250, 0))
        self.side_contents.setMaximumSize(QtCore.QSize(250, 16777215))

    def mousePressEvent(self, event):
        self.old_pos = event.globalPosition()

    def mouseMoveEvent(self, event):
        try:
            delta = event.globalPosition() - self.old_pos
        except TypeError:
            return
        self.move(int(self.x() + delta.x()), int(self.y() + delta.y()))
        self.old_pos = event.globalPosition()

    def closeEvent(self, event):
        self.queue_out.put({"method": "logout"})

        if self.connection_thread:
            self.connection_thread = None

        event.accept()

    def set_online_user(self, user):
        item = QtWidgets.QListWidgetItem()
        item.username = user
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)

        widget = QtWidgets.QWidget()
        widget_user = QtWidgets.QLabel(user.login)
        widget_user.setWordWrap(True)
        widget_user.setFont(font)
        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.addWidget(widget_user)

        widget_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        widget_layout.setSpacing(0)
        widget_layout.setContentsMargins(5, 5, 5, 0)
        widget_user.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        widget_user.setStyleSheet(USERS)
        size_policy = widget_user.sizePolicy()
        size_policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Policy.Expanding)
        widget_user.setSizePolicy(size_policy)

        widget_layout.addStretch()
        widget.setLayout(widget_layout)
        item.setSizeHint(widget.sizeHint())

        self.online_users.addItem(item)
        self.online_users.setItemWidget(item, widget)
        self.online_users.scrollToBottom()
        self.online_users.itemClicked.connect(self.select_user)

    def set_message(self, from_user, message, sent_at):
        item = QtWidgets.QListWidgetItem()
        item.username = from_user
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(11)

        widget = QtWidgets.QWidget()
        if from_user == self.me.login:
            bar = f"{from_user} - {sent_at}"
        else:
            bar = f"{sent_at} - {from_user}"

        widget_message = QtWidgets.QLabel(f"{bar}\n\n{message}")
        widget_message.setMaximumWidth(500)
        widget_message.setWordWrap(True)
        widget_message.setFont(font)
        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.addWidget(widget_message)

        if from_user == self.me.login:
            widget_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            widget_message.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            widget_message.setStyleSheet(MESSAGES_MY)
        else:
            widget_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            widget_message.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            widget_message.setStyleSheet(MESSAGES_OTHER)

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
        if self.current_item:
            self.online_users.itemWidget(self.current_item).findChild(QtWidgets.QLabel).setStyleSheet(USERS)
        self.current_item = item
        self.online_users.itemWidget(item).findChild(QtWidgets.QLabel).setStyleSheet(USER_SELECTED)
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

            self.logged_user.setText("UNAUTHORIZED")
            self.status_text.setText("OFFLINE")
            self.status_icon.setStyleSheet(
                f"background-image: url({self.FILE_PATH}/icons/offline.png);\nbackground-position: center;\n"""
            )
            self.login.setText("Войти")
            self.new_message.clear()
            self.session_key.clear()
            self.hash.clear()

            self.current_item = None
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
        if not accepted_message:
            print("Warning: Can't find message to accept.")
            return
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
        self.status_text.setText("ONLINE")
        self.logged_user.setText(self.me.login)
        self.status_icon.setStyleSheet(
            f"background-image: url({self.FILE_PATH}/icons/online.png);\nbackground-position: center;\n"""
        )

        for user in self.online_users_list:
            self.set_online_user(user)
            for message in self.messages_list:
                self.add_message_to_user(message, user)
        self.current_item = self.online_users.item(0)
        self.online_users.itemWidget(self.current_item).findChild(QtWidgets.QLabel).setStyleSheet(USER_SELECTED)
        self.switch_to_user(self.online_users_list[0])

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
                if self.current_item.username == user_to_remove:
                    self.current_item = self.online_users.item(0)
                    self.select_user(self.current_item)
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
