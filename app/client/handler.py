import json

from app.crypto import Des, DiffieHellman, SHA1, RSA


class ClientHandler:
    handler_started = False
    handler_running = None

    def __init__(self, client, login, password, queue_in, queue_out):
        self.client = client
        self.login = login
        self.password = password
        self.online_users = []
        self.messages = []

        self.cid = None
        self.auth_token = None
        self.session_key = None

        self.diffie_hellman = None
        self.des = Des()
        self.rsa_encrypt = None
        self.rsa_decrypt = RSA()

        self.queue_in = queue_in
        self.queue_out = queue_out

        ClientHandler.handler_running = self
        ClientHandler.handler_started = True
        self.first_connect = True

    def handle_task(self, payload):
        match payload["method"]:
            case "logout":
                self.client.sendClose()
                return True
            case "send_message":
                self.send_message(payload["username"], payload["message"], payload["mid"], payload["sha1_hash"])
                return False

    def handle_message(self, payload):
        result = json.loads(payload.decode("utf-8"))
        print(f"Received message: {result}")

        match result["method"]:
            case "authorize":
                self.authorize(result)
            case "auth_success":
                self.after_auth(result)
            case "update_key":
                self.start_key_exchange()
            case "first_key_exchange":
                self.last_key_exchange(result)
            case "dh_accepted":
                self.dh_accepted()
            case "dh_denied", "auth_failed":
                self.close_connection()
            case "message_verification_done":
                self.message_accepted(result)
            case "message_verification_pending":
                self.message_pending(result)
            case "message_verification_failed":
                self.message_denied(result)
            case "user_messages":
                self.get_messages(result)
            case "online_users":
                self.set_online_users(result)
            case "user_joined":
                self.user_joined(result)
            case "user_left":
                self.user_left(result)
            case "new_message":
                self.new_message(result)

    def pack_and_send(self, **kwargs):
        request_json = json.dumps(kwargs)
        print(f"Sending message: {request_json}")
        self.client.sendMessage(request_json.encode("utf-8"))

    def authorize(self, result):
        self.cid = result["cid"]
        self.pack_and_send(
            method="authorize",
            login=self.login,
            password=self.password
        )

    def after_auth(self, result):
        self.auth_token = result["auth_token"]
        self.start_key_exchange()

    def start_key_exchange(self):
        self.diffie_hellman = None
        self.pack_and_send(
            method="first_key_exchange",
            auth_token=self.auth_token
        )

    def last_key_exchange(self, result):
        g, p = result["g"], result["p"]
        public_key = result["rsa_server_public_key"]

        self.rsa_encrypt = RSA(public_key=public_key)
        self.diffie_hellman = DiffieHellman(g, p)
        self.diffie_hellman.set_partial_key_from_remote(result["partial_key"])

        print(f"Session key: {self.diffie_hellman.session_key}")
        self.pack_and_send(
            method="last_key_exchange",
            auth_token=self.auth_token,
            partial_key=self.diffie_hellman.get_partial_key(),
            rsa_client_public_key=self.rsa_decrypt.public_key
        )

    def dh_accepted(self):
        self.des.set_key(self.diffie_hellman.session_key)
        self.queue_out.put({
            "method": "update_key",
            "session_key": self.des.key.key_bin
        })

        if not self.first_connect:
            return

        self.pack_and_send(
            method="user_messages",
            auth_token=self.auth_token
        )
        self.first_connect = False

    def get_messages(self, result):
        verified_messages = []
        bad_messages = []

        for message in result["messages"]:
            message[3] = self.des.decrypt(message[3])
            if self.rsa_decrypt.decrypt(message[5]) == SHA1(message[3]).to_hash():
                verified_messages.append(message)
            else:
                bad_messages.append(message)

        self.pack_and_send(
            method="report_bad_good",
            auth_token=self.auth_token,
            bad_messages=[m[0] for m in bad_messages],
            good_messages=[m[0] for m in verified_messages]
        )

        if 0 == len(verified_messages) < len(bad_messages):
            self.queue_out.put({"method": "close_connection"})
            return

        self.messages = verified_messages
        self.pack_and_send(
            method="online_users",
            auth_token=self.auth_token,
        )

    def close_connection(self):
        self.queue_out.put({"method": "close_connection"})

    def set_online_users(self, result):
        self.online_users = result["online_users"]

        self.queue_out.put({
            "method": "userdata",
            "login": self.login,
            "password": self.password,
            "online_users": self.online_users,
            "messages": self.messages
        })

    def user_left(self, result):
        self.online_users.remove(result["username"])

        self.queue_out.put({
            "method": "user_left",
            "username": result["username"]
        })

    def user_joined(self, result):
        if result["username"] not in self.online_users:
            self.online_users.append(result["username"])

            self.queue_out.put({
                "method": "user_joined",
                "username": result["username"]
            })

    def send_message(self, username, message, mid, sha1_hash):
        encrypted = self.des.encrypt(message)
        try:
            digital_signature = self.rsa_encrypt.encrypt(sha1_hash)
        except ValueError:
            return

        self.pack_and_send(
            method="send_message",
            auth_token=self.auth_token,
            to_user=username,
            message=encrypted,
            digital_signature=digital_signature,
            mid=mid
        )
        print(f"[CHAT] [ME -> {username}] : '{message}'")

    def message_accepted(self, result):
        self.queue_out.put({
            "method": "message_verification_done",
            "mid": result["mid"]
        })

    def message_denied(self, result):
        self.queue_out.put({
            "method": "message_verification_failed",
            "step": result["step"],
            "mid": result["mid"]
        })
        if result["step"] == "hash_server":
            self.start_key_exchange()

    def message_pending(self, result):
        self.queue_out.put({
            "method": "message_verification_pending",
            "mid": result["mid"],
            "old_mid": result["old_mid"]
        })

    def new_message(self, result):
        decrypted = self.des.decrypt(result["message"])
        sha1_hash = SHA1(decrypted).to_hash()
        sha1_hash_from_remote = self.rsa_decrypt.decrypt(result["digital_signature"])

        if sha1_hash == sha1_hash_from_remote:
            self.pack_and_send(
                method="message_verification_done",
                from_user=result["from_user"],
                auth_token=self.auth_token,
                mid=result["mid"]
            )
            self.queue_out.put({
                "method": "new_message",
                "from_user": result["from_user"],
                "message": decrypted,
                "sent_at": result["sent_at"],
                "mid": result["mid"],
                "sha1_hash": sha1_hash
            })
            print(f"[CHAT] [{result['from_user']} -> ME] : '{decrypted}'")
        else:
            self.pack_and_send(
                method="message_verification_failed",
                from_user=result["from_user"],
                mid=result["mid"],
                auth_token=self.auth_token
            )
            self.queue_out.put({
                "method": "message_verification_failed",
                "mid": result["mid"],
                "step": "client_hash"
            })
