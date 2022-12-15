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
    def __init__(self, mid, uid_from, uid_to, message, sent_at):
        self.mid = mid
        self.uid_from = uid_from
        self.uid_to = uid_to
        self.message = message
        self.sent_at = sent_at

    def __iter__(self):
        return (i for i in [self.mid_key(), self.from_key(), self.to_key(), self.message, self.sent_at])

    def mid_key(self):
        return str(self.mid).rjust(5, "0")

    def from_key(self):
        return str(self.uid_from).rjust(5, "0")

    def to_key(self):
        return str(self.uid_to).rjust(5, "0")
