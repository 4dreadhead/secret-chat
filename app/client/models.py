class Message:
    def __init__(self, from_user, to_user, text, sent_at):
        self.text = text
        self.hash = "in_development"
        self.from_user = from_user
        self.to_user = to_user
        self.sent_at = sent_at


class User:
    def __init__(self, login):
        self.login = login
        self.messages = []

    def add_message(self, message):
        self.messages.append(message)
