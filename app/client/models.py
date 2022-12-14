class Message:
    def __init__(self, from_user, text):
        self.text = text
        self.hash = "in_development"
        self.from_user = from_user


class User:
    def __init__(self, login):
        self.login = login
        self.messages = []

    def add_message(self, text, from_user):
        self.messages.append(Message(text, from_user))
