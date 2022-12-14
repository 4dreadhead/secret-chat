from autobahn.asyncio.websocket import WebSocketClientProtocol
from .handler import ClientHandler


class ChatClient(WebSocketClientProtocol):
    def __init__(self):
        super().__init__()
        self.handler = ClientHandler(self, "user3", "password")

    def onConnect(self, request):
        print(f"Connecting to server: {request.peer}")

    def onOpen(self):
        print("Connection opened.")

    def onMessage(self, payload, isBinary):
        self.handler.handle_message(payload)

    def onClose(self, wasClean, code, reason):
        print("Connection closed: {0}".format(reason))
