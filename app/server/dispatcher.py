import os
import sqlite3
import datetime
import json
from .models import User, Message
from app.crypto import RSA

PATH = os.path.realpath("")


class Dispatcher:
    def __init__(self):
        self.connections = []
        self.sql_conn = sqlite3.connect(f"{PATH}/app/server/server.db")
        self.color = -1
        self.cursor = self.sql_conn.cursor()
        self.create_db_tables()
        self.cursor.execute("SELECT * FROM users")
        self.users = [User(*result) for result in self.cursor.fetchall()]
        self.cursor.execute("SELECT mid, uid_from, uid_to, message, sent_at, sha1_hash FROM messages")
        self.messages = [Message(*result) for result in self.cursor.fetchall()]
        self.rsa_main = RSA()

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
                mid INTEGER PRIMARY KEY AUTOINCREMENT,
                uid_from TEXT,
                uid_to TEXT,
                message TEXT,
                sent_at TEXT,
                sha1_hash TEXT,
                bad_score INTEGER DEFAULT 0
            )
        """)
        # self.cursor.execute("""
        #     ALTER TABLE messages ADD COLUMN bad_score INT DEFAULT 0
        # """)
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

    def current_color(self):
        self.color = (self.color + 1) % 6
        return 7 - (self.color + 1)

    def online_users(self):
        return list(set([conn.user.login for conn in self.connections if conn.user]))

    def create_user(self, login, password):
        new_user = User((len(self.users) + 1), login, password, "active")
        self.cursor.execute("INSERT INTO users VALUES(?, ?, ?, ?)", tuple(new_user))
        self.sql_conn.commit()
        self.users.append(new_user)

        return new_user

    def send_message(self, from_user, to_user, message, sha1_hash):
        sent_at = datetime.datetime.now().strftime("%d.%m.%y %H:%M")
        new_message = Message(None, from_user, to_user, message, sent_at, sha1_hash)
        self.cursor.execute(
            f"INSERT INTO messages (uid_from, uid_to, message, sent_at, sha1_hash) VALUES {tuple(new_message)}"
        )
        new_message.mid = self.cursor.lastrowid
        self.sql_conn.commit()
        self.messages.append(new_message)
        for conn in self.connections:
            if conn.user.login == to_user:
                conn.new_message(from_user, message, sent_at, sha1_hash, int(new_message.mid))
        return new_message.mid

    def accept_message(self, from_user, mid):
        print(f"Accepting message from user {from_user}")
        for conn in self.connections:
            if conn.user.login == from_user:
                conn.accept_message(mid)

    def deny_message(self, from_user, mid):
        for conn in self.connections:
            if conn.user.login == from_user:
                conn.deny_message(mid)

    def user_messages(self, user):
        self.cursor.execute(f"""
        SELECT mid, uid_from, uid_to, message, sent_at, sha1_hash
        FROM messages
        WHERE (uid_from = '{user.login}' OR uid_to = '{user.login}') AND bad_score < 3
        """)
        return [list(Message(*result)) for result in self.cursor.fetchall()]

    def bad_messages(self, messages):
        if not messages:
            return

        self.cursor.execute(
            f"UPDATE messages SET bad_score = bad_score + 1 WHERE mid IN {str(tuple(messages)).replace(',)', ')')};"
        )
        self.sql_conn.commit()

    def good_messages(self, messages):
        if not messages:
            return

        self.cursor.execute(
            f"UPDATE messages SET bad_score = 0 WHERE mid IN {str(tuple(messages)).replace(',)', ')')};"
        )
        self.sql_conn.commit()

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
