# Custom models for server

class User:
    def __init__(self, uid, login, password, status):
        self.uid = int(uid)
        self.login = login
        self.password = password
        self.status = status

    def __iter__(self):
        return (i for i in [str(self.uid).rjust(5, "0"), self.login, self.password, self.status])
