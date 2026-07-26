"""Test ConnectionManager with fake WebSocket-like objects — no FastAPI needed."""
import asyncio
from ws_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self, fail_on_send=False):
        self.sent = []
        self.fail_on_send = fail_on_send
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, msg):
        if self.fail_on_send:
            raise RuntimeError("connection closed")
        self.sent.append(msg)


async def test_broadcast_reaches_all_connected():
    manager = ConnectionManager()
    ws1, ws2 = FakeWebSocket(), FakeWebSocket()
    await manager.connect(ws1)
    await manager.connect(ws2)
    await manager.broadcast("TRIGGER_BREAK")
    assert ws1.sent == ["TRIGGER_BREAK"]
    assert ws2.sent == ["TRIGGER_BREAK"]
    print("PASS: broadcast reaches all connected clients")


async def test_disconnect_stops_future_broadcasts():
    manager = ConnectionManager()
    ws1 = FakeWebSocket()
    await manager.connect(ws1)
    manager.disconnect(ws1)
    await manager.broadcast("TRIGGER_BREAK")
    assert ws1.sent == [], f"expected no messages after disconnect, got {ws1.sent}"
    print("PASS: disconnected client receives nothing")


async def test_broken_connection_is_dropped_automatically():
    manager = ConnectionManager()
    good, bad = FakeWebSocket(), FakeWebSocket(fail_on_send=True)
    await manager.connect(good)
    await manager.connect(bad)
    await manager.broadcast("TRIGGER_BREAK")
    assert good.sent == ["TRIGGER_BREAK"]
    assert bad not in manager._connections, "a broken connection should be dropped automatically"
    print("PASS: a broken connection is dropped without affecting other clients")


async def main():
    await test_broadcast_reaches_all_connected()
    await test_disconnect_stops_future_broadcasts()
    await test_broken_connection_is_dropped_automatically()


asyncio.run(main())
