import json
import base64


class ConnectionHandler:
    def __init__(self, chat_server, dp):
        self.connection = chat_server
        self.dispatcher = dp

        self.user = None
        self.cid = None
        self.auth_token = None
        self.session_key = None

    def handle_message(self, message):
        try:
            result = json.loads(message.decode("utf-8"))
        except json.decoder.JSONDecodeError:
            self.unknown_request()
            return

        try:
            match result["method"]:
                case "authorize":
                    self.authorize_client(result)
                case "online_users":
                    self.online_users(result)
                case "send_message":
                    self.send_message(result)
                case _:
                    self.unknown_request()
        except KeyError:
            self.unknown_request()

    def pack_and_send(self, **kwargs):
        self.connection.sendMessage(json.dumps(kwargs).encode("utf-8"))

    def verify_fields(self, result, *fields):
        for field in fields:
            try:
                _ = result[field]
            except KeyError:
                self.bad_request(result["method"], field)
                return False

        return True

    def unknown_request(self):
        self.pack_and_send(method="unknown_request")

    def bad_request(self, method, missed_field):
        self.pack_and_send(method="bad_request", failed_method=method, missed_field=missed_field)

    def first_connect(self):
        self.pack_and_send(method="authorize", cid=self.cid)

    def authorize_client(self, result):
        if not self.verify_fields(result, "login", "password"):
            return

        found_user = self.dispatcher.find_user(by="login", key=result["login"])

        if found_user:
            self.user = found_user
        else:
            self.user = self.dispatcher.create_user(result["login"], result["password"])

        if not self.user.password == result["password"]:
            self.auth_failed()
            return

        self.auth_success()
        self.dispatcher.broadcast_user_joined(self.user.login)

    def auth_success(self):
        # TODO: add symmetric session key
        self.auth_token = self.generate_auth_token()
        self.session_key = "in_development"
        self.pack_and_send(
            method="auth_success",
            auth_token=self.auth_token,
            session_key=self.session_key
        )

    def generate_auth_token(self):
        auth_token = json.dumps(
            {
                "cid": self.cid,
                "uid": self.user.uid,
            }
        )
        return base64.b64encode(auth_token.encode("utf-8")).decode("utf-8")

    def verify_auth_token(self, result):
        try:
            auth_token = result["auth_token"]
        except KeyError:
            return self.auth_failed()

        return True if self.auth_token and self.auth_token == auth_token else self.auth_failed()

    def auth_failed(self):
        self.pack_and_send(method="auth_failed")
        self.connection.sendClose(reason="auth_failed", code=4003)

        return False

    def online_users(self, result):
        if not self.verify_auth_token(result):
            return

        online_users = self.dispatcher.online_users()
        self.pack_and_send(method="online_users", online_users=online_users)

    def user_joined(self, new_user):
        self.pack_and_send(
            method="user_joined",
            username=new_user
        )

    def user_left(self, left_user):
        self.pack_and_send(
            method="user_left",
            username=left_user
        )

    def send_message(self, result):
        if not self.verify_fields(result, "to_user", "message"):
            return

        if not self.verify_auth_token(result):
            return

        self.dispatcher.send_message(self.user.login, result["to_user"], result["message"])

    def new_message(self, from_user, message):
        # TODO: add encryption
        self.pack_and_send(
            method="new_message",
            from_user=from_user,
            message=message
        )
