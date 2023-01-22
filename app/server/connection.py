import uuid
from autobahn.asyncio.websocket import WebSocketServerProtocol
from .handler import ConnectionHandler


class ChatServer(WebSocketServerProtocol):
    def __init__(self, dp):
        super().__init__()
        self.handler = ConnectionHandler(self, dp)
        self.color = "7"

    async def onConnect(self, request):
        print(f"\033[37mClient connecting: {request.peer}")

    async def onOpen(self):
        self.handler.cid = str(uuid.uuid4())
        self.color = self.handler.dispatcher.current_color()
        print(f"\033[3{self.color}mConnection opened: {self.handler.cid}")

        self.handler.color = self.color
        self.handler.dispatcher.connections.append(self.handler)
        self.handler.first_connect()

    async def onMessage(self, payload, *args):
        print(f"\033[3{self.color}mReceived message: {payload.decode('utf-8')}")
        self.handler.handle_message(payload)

    async def onClose(self, wasClean, code, reason):
        print(f"\033[3{self.color}mConnection {self.handler.cid} closed.")
        self.handler.dispatcher.connections.remove(self.handler)
        if self.handler.user:
            self.handler.dispatcher.broadcast_user_left(self.handler.user.login)
