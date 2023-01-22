# Custom models for server

class User:
    def __init__(self, uid, login, password, status):
        self.uid = int(uid)
        self.login = login
        self.password = password
        self.status = status

    def __iter__(self):
        return (i for i in [self.uid_key(), self.login, self.password, self.status])

    def uid_key(self):
        return str(self.uid).rjust(5, "0")


class Message:
    def __init__(self, mid, uid_from, uid_to, message, sent_at, sha1_hash):
        try:
            self.mid = int(mid)
        except TypeError:
            self.mid = mid
        self.uid_from = uid_from
        self.uid_to = uid_to
        self.message = message
        self.sent_at = sent_at
        self.sha1_hash = sha1_hash

    def __iter__(self):
        if self.mid:
            return (i for i in
                    [self.mid_key(), self.uid_from, self.uid_to, self.message, self.sent_at, self.sha1_hash])
        else:
            return (i for i in
                    [self.uid_from, self.uid_to, self.message, self.sent_at, self.sha1_hash])

    def mid_key(self):
        return str(self.mid).rjust(5, "0")

    @staticmethod
    def find(msg_list, msg_id):
        result = None
        for msg in msg_list:
            if msg.mid == msg_id:
                result = msg
                break
        return result

