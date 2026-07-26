"""
ws_manager.py — Tracks connected WebSocket clients and broadcasts
messages to all of them.

Deliberately has NO import of FastAPI/Starlette — it only needs any
object with async accept()/send_text() methods, real or fake. Same
separation-of-concerns idea as Day 3's deferred pynput import: keep
the trickiest logic (broadcasting to multiple clients, handling one
that's disconnected mid-broadcast) testable on its own.
"""

import threading


class ConnectionManager:
    def __init__(self):
        self._connections = []
        self._lock = threading.Lock()

    async def connect(self, ws):
        await ws.accept()
        with self._lock:
            self._connections.append(ws)

    def disconnect(self, ws):
        with self._lock:
            if ws in self._connections:
                self._connections.remove(ws)

    async def broadcast(self, message: str):
        with self._lock:
            targets = list(self._connections)
        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception:
                self.disconnect(ws)
