from autobahn.asyncio.websocket import WebSocketClientProtocol
from .handler import ClientHandler
import asyncio
from autobahn.asyncio.websocket import WebSocketClientFactory


class ChatClient(WebSocketClientProtocol):
    def __init__(self, login, password, loop, queue_in, queue_out):
        super().__init__()
        self.handler = ClientHandler(self, login, password, queue_in, queue_out)
        self.loop = loop

    async def onConnect(self, request):
        print(f"Connecting to server: {request.peer}")

    async def onOpen(self):
        print("Connection opened.")

    async def onMessage(self, payload, isBinary):
        self.handler.handle_message(payload)

    async def onClose(self, wasClean, code, reason):
        self.handler.close_connection()
        self.loop.shutdown_asyncgens()


async def check_queue():
    while True:
        await asyncio.sleep(0.15)
        if ClientHandler.handler_started:
            handler = ClientHandler.handler_running
            break

    while True:
        if handler.queue_in.empty():
            await asyncio.sleep(0.15)
            continue

        payload = handler.queue_in.get()
        handler.handle_task(payload)
        handler.queue_in.task_done()


async def async_tasks(conn, task):
    await asyncio.gather(conn, task)


def run_client(login, password, queue_in, queue_out):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    factory = WebSocketClientFactory("ws://127.0.0.1:8080")
    factory.protocol = lambda: ChatClient(login, password, loop, queue_in, queue_out)

    conn = loop.create_connection(factory, '127.0.0.1', 8080)
    task = loop.create_task(check_queue())

    loop.run_until_complete(async_tasks(conn, task))
    loop.run_forever()
    loop.close()
