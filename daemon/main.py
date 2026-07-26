"""
main.py — FastAPI wrapper around the daemon.

Endpoints:
  GET  /               health check
  WS   /ws              real-time TRIGGER_BREAK messages, for the React dashboard
  POST /break-outcome   the dashboard reports "completed" or "snoozed" here

Run with:
    uvicorn main:app --host 0.0.0.0 --port 8000

Starts the same tracker + pynput wiring daemon.py uses, but as part of
FastAPI's lifespan, so this one process is the entire local daemon.
"""

import asyncio
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from tracker import ActivityTracker
from db import init_db
from daemon import log_event, start_listeners
from ws_manager import ConnectionManager

manager = ConnectionManager()
main_loop = None  # set once FastAPI's event loop is running (see lifespan below)


def on_trigger_break():
    print("[daemon] TRIGGER_BREAK")
    log_event("break_triggered")
    if main_loop is not None:
        # on_trigger_break runs on the tracker's background thread, not
        # the asyncio event loop — run_coroutine_threadsafe is the safe
        # bridge between the two. Verified independently in
        # test_cross_thread_broadcast.py.
        asyncio.run_coroutine_threadsafe(manager.broadcast("TRIGGER_BREAK"), main_loop)


def on_go_idle():
    print("[daemon] went idle")
    log_event("went_idle")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    main_loop = asyncio.get_running_loop()

    init_db()
    tracker = ActivityTracker(on_trigger_break=on_trigger_break, on_go_idle=on_go_idle)
    app.state.tracker = tracker

    keyboard_listener, mouse_listener = start_listeners(tracker)
    tracker_thread = threading.Thread(target=tracker.run, daemon=True)
    tracker_thread.start()

    yield  # app runs here

    tracker.stop()
    keyboard_listener.stop()
    mouse_listener.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health():
    return {"status": "running"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep the connection open; no incoming messages expected
    except WebSocketDisconnect:
        manager.disconnect(ws)


class BreakOutcome(BaseModel):
    outcome: str  # "completed" or "snoozed"


@app.post("/break-outcome")
def break_outcome(payload: BreakOutcome):
    app.state.tracker.acknowledge_break()
    log_event(f"break_{payload.outcome}")
    return {"status": "ok"}
