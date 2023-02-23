import json
import base64
from app.crypto import Des, SHA1, RSA, DiffieHellman


class ConnectionHandler:
    def __init__(self, chat_server, dp):
        self.connection = chat_server
        self.dispatcher = dp
        self.color = None

        self.diffie_hellman = None
        self.des = Des()
        self.rsa_client = None

        self.user = None
        self.cid = None
        self.auth_token = None
        self.session_key = None

        self.connection_locked = True

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
                case "user_messages":
                    self.user_messages(result)
                case "first_key_exchange":
                    self.first_key_exchange(result)
                case "last_key_exchange":
                    self.last_key_exchange(result)
                case "send_message":
                    self.send_message(result)
                case "message_verification_done":
                    self.send_accept_message(result)
                case "message_verification_failed":
                    self.send_deny_message(result)
                case "report_bad_good":
                    self.bad_good(result)
                case _:
                    self.unknown_request()
        except KeyError:
            self.unknown_request()

    def pack_and_send(self, **kwargs):
        message = json.dumps(kwargs).encode("utf-8")
        print(f"\033[3{self.color}mSending message: {message}")
        self.connection.sendMessage(message)

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
        self.auth_token = self.generate_auth_token()
        self.pack_and_send(
            method="auth_success",
            auth_token=self.auth_token
        )

    def first_key_exchange(self, result):
        if not self.verify_auth_token(result):
            return

        self.diffie_hellman = DiffieHellman()

        self.pack_and_send(
            method="first_key_exchange",
            g=self.diffie_hellman.get_g(),
            p=self.diffie_hellman.get_p(),
            partial_key=self.diffie_hellman.get_partial_key(),
            rsa_server_public_key=self.dispatcher.rsa_main.public_key
        )

    def last_key_exchange(self, result):
        if not self.verify_auth_token(result):
            return

        if not self.verify_fields(result, "partial_key", "rsa_client_public_key"):
            return

        try:
            partial_key = int(result["partial_key"], 16)
            if partial_key not in range(1, self.diffie_hellman.p):
                raise ValueError
            self.rsa_client = RSA(public_key=result["rsa_client_public_key"])
            self.rsa_client.encrypt("abc123")

        except (ValueError, TypeError):
            self.pack_and_send(method="dh_denied")
            return

        self.diffie_hellman.set_partial_key_from_remote(result["partial_key"])
        self.des.set_key(self.diffie_hellman.session_key)
        self.pack_and_send(method="dh_accepted")
        self.connection_locked = False

        print(f"\033[3{self.color}m--- [ DIFFIE-HELLMAN FINISHED ] ---")
        print(f"\033[3{self.color}mSession key: {''.join([format(b, '02x') for b in self.diffie_hellman.session_key])}")
        print(f"\033[3{self.color}m-----------------------------------")

    def generate_auth_token(self):
        auth_token = json.dumps({
            "cid": self.cid,
            "uid": self.user.uid,
        })
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

    def bad_good(self, result):
        print(f"\033[3{self.color}m--- [ CLIENT BAD MESSAGES REPORT ] ---")
        print(f"\033[3{self.color}mBAD  messages {result['bad_messages']}")
        print(f"\033[3{self.color}mGOOD messages {result['good_messages']}")
        print(f"\033[3{self.color}m--------------------------------------")
        self.dispatcher.bad_messages(result['bad_messages'])
        self.dispatcher.good_messages(result['good_messages'])

    def online_users(self, result):
        if not self.verify_auth_token(result):
            return

        online_users = self.dispatcher.online_users()
        self.pack_and_send(method="online_users", online_users=online_users)

    def user_messages(self, result):
        if not self.verify_auth_token(result):
            return

        messages = self.dispatcher.user_messages(self.user)
        for message in messages:
            message[3] = self.des.encrypt(message[3])
            # message[5] = self.rsa_client.encrypt(message[5])
            message[5] = self.dispatcher.rsa_main.encrypt_signature(message[5])
        self.pack_and_send(method="user_messages", messages=messages)

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
        if self.connection_locked:
            self.pack_and_send(method="update_key")
            return

        if not self.verify_fields(result, "mid", "to_user", "message", "digital_signature"):
            return

        if not self.verify_auth_token(result):
            return

        decrypted = self.des.decrypt(result["message"])
        sha1_hash = SHA1(decrypted).to_hash()
        # sha1_hash_from_remote = self.dispatcher.rsa_main.decrypt(result["digital_signature"])
        sha1_hash_from_remote = self.rsa_client.decrypt_signature(result["digital_signature"])

        if sha1_hash == sha1_hash_from_remote:
            message_id = self.dispatcher.send_message(self.user.login, result["to_user"], decrypted, sha1_hash)
            self.pack_and_send(
                method="message_verification_pending",
                mid=message_id,
                old_mid=result["mid"]
            )
        else:
            self.pack_and_send(
                method="message_verification_failed",
                step="hash_server",
                mid=result["mid"]
            )
            self.connection_locked = True
            print(f"\033[3{self.color}m--- [ FAILED DECRYPTING MESSAGE ] ---")
            print(f"\033[3{self.color}mciphertext: {result['message']}")
            print(f"\033[3{self.color}mdecrypted: {decrypted}")
            print(f"\033[3{self.color}msha1_hash from remote: {sha1_hash_from_remote}")
            print(f"\033[3{self.color}msha1_hash calculated:  {sha1_hash}")
            print(f"\033[3{self.color}mdes key: {''.join([format(b, '02x') for b in self.des.key.key_bytes])}")
            print(f"\033[3{self.color}m-------------------------------------")

    def send_accept_message(self, result):
        if not self.verify_auth_token(result):
            return

        if not self.verify_fields(result, "from_user", "mid"):
            return

        self.dispatcher.accept_message(result["from_user"], result["mid"])

    def send_deny_message(self, result):
        if not self.verify_auth_token(result):
            return

        if not self.verify_fields(result, "from_user", "mid"):
            return

        self.pack_and_send(method="update_key")
        self.connection_locked = True
        self.dispatcher.deny_message(result["from_user"], result["mid"])

    def accept_message(self, mid):
        self.pack_and_send(
            method="message_verification_done",
            mid=mid
        )

    def deny_message(self, mid):
        self.pack_and_send(
            method="message_verification_failed",
            step="client_hash",
            mid=mid
        )

    def new_message(self, from_user, message, sent_at, sha1_hash, message_id):
        encrypted = self.des.encrypt(message)
        # digital_signature = self.rsa_client.encrypt(sha1_hash)
        digital_signature = self.dispatcher.rsa_main.encrypt_signature(sha1_hash)
        self.pack_and_send(
            method="new_message",
            from_user=from_user,
            message=encrypted,
            sent_at=sent_at,
            digital_signature=digital_signature,
            mid=message_id
        )
