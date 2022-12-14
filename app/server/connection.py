import uuid
from autobahn.asyncio.websocket import WebSocketServerProtocol
from .handler import ConnectionHandler


class ChatServer(WebSocketServerProtocol):
    def __init__(self, dp):
        super().__init__()
        self.handler = ConnectionHandler(self, dp)

    async def onConnect(self, request):
        print(f"Client connecting: {request.peer}")

    async def onOpen(self):
        self.handler.cid = str(uuid.uuid4())
        print(f"Connection opened: {self.handler.cid}")

        self.handler.dispatcher.connections.append(self.handler)
        self.handler.first_connect()

    async def onMessage(self, payload, *args):
        print(f"Received message: {payload.decode('utf-8')}")
        self.handler.handle_message(payload)

    async def onClose(self, wasClean, code, reason):
        print(f"Connection {self.handler.cid} closed.")
        self.handler.dispatcher.connections.remove(self.handler)
        if self.handler.user:
            self.handler.dispatcher.broadcast_user_left(self.handler.user.login)
