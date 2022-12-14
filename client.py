import asyncio
import sys
import threading

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from threading import Thread
from autobahn.asyncio.websocket import WebSocketClientFactory
from app.client.connection import ChatClient


def run_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    factory = WebSocketClientFactory("ws://127.0.0.1:8080")
    factory.protocol = ChatClient

    coro = loop.create_connection(factory, '127.0.0.1', 8080)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()


if __name__ == '__main__':
    t = threading.Thread(target=run_client)
    t.start()
    t.join()
