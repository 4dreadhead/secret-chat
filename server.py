import asyncio
from autobahn.asyncio.websocket import WebSocketServerFactory
from app.server.dispatcher import Dispatcher
from app.server.connection import ChatServer


def run_server():
    dispatcher = Dispatcher()
    factory = WebSocketServerFactory(f"ws://127.0.0.1:8080")
    factory.protocol = lambda: ChatServer(dispatcher)

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, "127.0.0.1", 8080)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()


if __name__ == '__main__':
    run_server()
