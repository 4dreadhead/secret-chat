import asyncio
import json


class ClientHandler:
    handler_started = False
    handler_running = None

    def __init__(self, client, login, password, queue_in, queue_out):
        self.client = client
        self.login = login
        self.password = password
        self.online_users = []

        self.cid = None
        self.auth_token = None
        self.session_key = None

        self.queue_in = queue_in
        self.queue_out = queue_out

        ClientHandler.handler_running = self
        ClientHandler.handler_started = True

    def handle_task(self, payload):
        match payload["method"]:
            case "logout":
                self.client.sendClose()
                return True
            case "send_message":
                self.send_message(payload["username"], payload["message"])
                return False

    def handle_message(self, payload):
        result = json.loads(payload.decode("utf-8"))
        print(f"Received message: {result}")

        match result["method"]:
            case "authorize":
                self.authorize(result)
            case "auth_success":
                self.after_auth(result)
            case "auth_failed":
                pass
            case "online_users":
                self.set_online_users(result)
            case "user_joined":
                self.user_joined(result)
            case "user_left":
                self.user_left(result)
            case "new_message":
                self.new_message(result)
            case "send_message":
                pass

    def pack_and_send(self, **kwargs):
        self.client.sendMessage(json.dumps(kwargs).encode("utf-8"))

    def authorize(self, result):
        self.cid = result["cid"]
        self.pack_and_send(
            method="authorize",
            login=self.login,
            password=self.password
        )

    def after_auth(self, result):
        self.auth_token = result["auth_token"]
        self.session_key = result["session_key"]

        self.pack_and_send(
            method="online_users",
            auth_token=self.auth_token,
        )

    def close_connection(self):
        self.queue_out.put(
            {
                "method": "close_connection"
            }
        )

    def set_online_users(self, result):
        self.online_users = result["online_users"]

        self.queue_out.put(
            {
                "method": "userdata",
                "login": self.login,
                "password": self.password,
                "online_users": self.online_users,
                "session_key": self.session_key
            }
        )

    def user_left(self, result):
        self.online_users.remove(result["username"])

        self.queue_out.put(
            {
                "method": "user_left",
                "username": result["username"]
            }
        )

    def user_joined(self, result):
        if result["username"] not in self.online_users:
            self.online_users.append(result["username"])

            self.queue_out.put(
                {
                    "method": "user_joined",
                    "username": result["username"]
                }
            )

    def update_key(self, result):
        # TODO: add public key updating
        self.auth_token = result["auth_token"]
        keys_pair = {"public": "in_development"}
        self.pack_and_send(
            method="update_key",
            auth_token=self.auth_token,
            public_key=keys_pair["public"]
        )

    def send_message(self, username, message):
        # TODO: add encrypting messages
        self.pack_and_send(
            method="send_message",
            auth_token=self.auth_token,
            to_user=username,
            message=message
        )
        print(f"[CHAT] [ME -> {username}] : '{message}'")

    def new_message(self, result):
        # TODO: add decrypting messages
        print(f"[CHAT] [{result['from_user']} -> ME] : '{result['message']}'")

        self.queue_out.put(
            {
                "method": "new_message",
                "from_user": result["from_user"],
                "message": result["message"]
            }
        )
