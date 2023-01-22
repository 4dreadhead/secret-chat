class Message:
    def __init__(self, mid, from_user, to_user, text, sent_at, sha1_hash):
        try:
            self.mid = int(mid)
        except ValueError:
            self.mid = mid
        self.text = text
        self.sha1_hash = sha1_hash
        self.from_user = from_user
        self.to_user = to_user
        self.sent_at = sent_at

    @staticmethod
    def find(messages_list, mid):
        result = None
        for message in messages_list:
            if message.mid == mid:
                result = message
                break

        return result


class User:
    def __init__(self, login):
        self.login = login
        self.messages = []

    def add_message(self, message):
        self.messages.append(message)

    @staticmethod
    def find(user_list, login):
        result = None
        for user in user_list:
            if user.login == login:
                result = user
                break

        return result
