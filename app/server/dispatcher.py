import os
import sqlite3
import datetime
from .models import User, Message

PATH = os.path.realpath("")


class Dispatcher:
    def __init__(self):
        self.connections = []
        self.sql_conn = sqlite3.connect(f"{PATH}/app/server/server.db")
        self.cursor = self.sql_conn.cursor()
        self.create_db_tables()
        self.cursor.execute("SELECT * FROM users")
        self.users = [User(*result) for result in self.cursor.fetchall()]
        self.cursor.execute("SELECT * FROM messages")
        self.messages = [Message(*result) for result in self.cursor.fetchall()]

    def create_db_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users(
                uid INT PRIMARY KEY,
                login TEXT,
                password TEXT,
                status TEXT
            );
        """)
        self.sql_conn.commit()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages(
                mid INT PRIMARY KEY,
                uid_from INT,
                uid_to INT,
                message TEXT,
                sent_at TEXT
            )
        """)
        self.sql_conn.commit()

    def find_user(self, by="uid", key=None):
        result = None

        match by:
            case "uid":
                for user in self.users:
                    if user.uid == key:
                        result = user
            case "login":
                for user in self.users:
                    if user.login == key:
                        result = user

        return result

    def online_users(self):
        return list(set([conn.user.login for conn in self.connections if conn.user]))

    def create_user(self, login, password):
        new_user = User((len(self.users) + 1), login, password, "active")
        self.cursor.execute("INSERT INTO users VALUES(?, ?, ?, ?)", tuple(new_user))
        self.sql_conn.commit()
        self.users.append(new_user)

        return new_user

    def send_message(self, from_user, to_user, message):
        sent_at = datetime.datetime.now().strftime("%d.%m.%y %H:%M")
        new_message = Message(len(self.messages) + 1, from_user, to_user, message, sent_at)
        self.cursor.execute("INSERT INTO messages VALUES(?, ?, ?, ?, ?)", tuple(new_message))
        self.sql_conn.commit()
        self.messages.append(message)
        for conn in self.connections:
            if conn.user.login == to_user:
                conn.new_message(from_user, message, sent_at)

    def user_messages(self, user):
        self.cursor.execute(f"SELECT * FROM messages WHERE uid_from = '{user.login}' OR uid_to = '{user.login}'")
        return [list(Message(*result)) for result in self.cursor.fetchall()]

    def broadcast_user_joined(self, new_user):
        for conn in self.connections:
            if conn.user.login == new_user:
                continue

            conn.user_joined(new_user)

    def broadcast_user_left(self, left_user):
        for conn in self.connections:
            if conn.user.login == left_user:
                return

        for conn in self.connections:
            conn.user_left(left_user)
