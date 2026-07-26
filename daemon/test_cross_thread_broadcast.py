"""
Verifies the exact concurrency pattern main.py depends on: a
background thread (standing in for the tracker's tick loop) using
asyncio.run_coroutine_threadsafe() to safely hand a message to code
running on the main asyncio event loop (standing in for the WebSocket
broadcast). Stdlib only — this isolates and proves the risky part
independent of FastAPI, which isn't available in this sandbox.
"""
import asyncio
import threading
import time

from ws_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self):
        self.sent = []

    async def accept(self):
        pass

    async def send_text(self, msg):
        self.sent.append(msg)


def test_background_thread_can_trigger_broadcast_on_event_loop():
    manager = ConnectionManager()
    fake_client = FakeWebSocket()
    loop_ref = {}
    done = threading.Event()

    async def app_main():
        loop_ref["loop"] = asyncio.get_running_loop()
        await manager.connect(fake_client)
        # simulate the app staying alive while the background thread works
        await asyncio.sleep(1.0)

    def background_thread_work():
        # wait for the loop to be ready, same as main.py waiting for
        # startup to finish before the tracker thread can broadcast
        while "loop" not in loop_ref:
            time.sleep(0.01)
        # this is the exact call on_trigger_break() makes from the
        # tracker's background thread in the real daemon
        asyncio.run_coroutine_threadsafe(
            manager.broadcast("TRIGGER_BREAK"), loop_ref["loop"]
        )
        done.set()

    t = threading.Thread(target=background_thread_work)
    t.start()
    asyncio.run(app_main())
    t.join()

    assert done.is_set()
    assert fake_client.sent == ["TRIGGER_BREAK"], (
        f"expected the background thread's broadcast to reach the client, got {fake_client.sent}"
    )
    print("PASS: background thread can safely trigger a broadcast on the event loop")


test_background_thread_can_trigger_broadcast_on_event_loop()
