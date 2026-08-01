"""
main.py — FastAPI wrapper around the daemon.

Endpoints:
  GET  /               health check
  WS   /ws              real-time TRIGGER_BREAK messages, for the React dashboard
  POST /break-outcome   the dashboard reports "completed" or "snoozed" here

Run with either:
    python3 main.py
    uvicorn main:app --host 0.0.0.0 --port 8000

Host/port/thresholds all come from config.py (env vars), not
hardcoded here — see .env.example for what's adjustable.

Starts the same tracker + pynput wiring daemon.py uses, but as part of
FastAPI's lifespan, so this one process is the entire local daemon.
"""

import asyncio
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from pydantic import BaseModel

import config
from tracker import ActivityTracker
from db import init_db
from daemon import log_event, log_session, start_listeners
from ws_manager import ConnectionManager
from wellness import compute_daily_wellness
import analytics

logger = logging.getLogger(__name__)

manager = ConnectionManager()
main_loop = None  # set once FastAPI's event loop is running (see lifespan below)


def on_trigger_break():
    logger.info("TRIGGER_BREAK")
    log_event("break_triggered")
    if main_loop is not None:
        # on_trigger_break runs on the tracker's background thread, not
        # the asyncio event loop — run_coroutine_threadsafe is the safe
        # bridge between the two. Verified independently in
        # test_cross_thread_broadcast.py.
        asyncio.run_coroutine_threadsafe(manager.broadcast("TRIGGER_BREAK"), main_loop)


def on_go_idle():
    logger.info("went idle")
    log_event("went_idle")


def on_session_end(duration_seconds, reason):
    logger.info(f"session ended: {duration_seconds:.0f}s ({reason})")
    log_session(duration_seconds, reason)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    config.setup_logging()
    main_loop = asyncio.get_running_loop()

    init_db()
    tracker = ActivityTracker(
	on_trigger_break=on_trigger_break,
    	on_go_idle=on_go_idle,
    	on_session_end=on_session_end,
    	idle_timeout=config.IDLE_TIMEOUT_SECONDS,
    	continuous_threshold=config.CONTINUOUS_THRESHOLD_SECONDS,
    	check_interval=config.CHECK_INTERVAL_SECONDS,
    )
    app.state.tracker = tracker

    keyboard_listener, mouse_listener = start_listeners(tracker)
    tracker_thread = threading.Thread(target=tracker.run, daemon=True)
    tracker_thread.start()
    logger.info(f"daemon started (device_id={config.DEVICE_ID})")

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
    if payload.outcome == "completed":
        # a real break — ends the session, starts a fresh streak
        app.state.tracker.acknowledge_break()
    elif payload.outcome == "snoozed":
        # NOT a real break — suppresses the reminder for a grace period
        # but the session (and the unhealthy streak) keeps running
        app.state.tracker.snooze_break(config.SNOOZE_GRACE_SECONDS)
    log_event(f"break_{payload.outcome}")
    return {"status": "ok"}


@app.get("/wellness/today")
def wellness_today():
    result = compute_daily_wellness(config.DEVICE_ID)
    return {
        "date": result.date,
        "score": result.score,
        "fatigue_risk": result.fatigue_risk,
        "reasons": result.reasons,
        "healthy_breaks": result.healthy_breaks,
        "daily_goal": result.daily_goal,
        "longest_session_seconds": result.longest_session_seconds,
        "average_session_seconds": result.average_session_seconds,
    }


@app.get("/analytics/timeline")
def health_timeline(start_date: str, end_date: str):
    return analytics.get_health_timeline(config.DEVICE_ID, start_date, end_date)


@app.get("/reports/weekly")
def weekly_report():
    return analytics.generate_report(config.DEVICE_ID, days=7)


@app.get("/reports/monthly")
def monthly_report():
    return analytics.generate_report(config.DEVICE_ID, days=30)


@app.get("/reports/weekly/export")
def export_weekly(format: str = "json"):
    report = analytics.generate_report(config.DEVICE_ID, days=7)
    if format == "csv":
        return Response(content=analytics.export_report_csv(report), media_type="text/csv")
    return Response(content=analytics.export_report_json(report), media_type="application/json")


@app.get("/reports/monthly/export")
def export_monthly(format: str = "json"):
    report = analytics.generate_report(config.DEVICE_ID, days=30)
    if format == "csv":
        return Response(content=analytics.export_report_csv(report), media_type="text/csv")
    return Response(content=analytics.export_report_json(report), media_type="application/json")


if __name__ == "__main__":
    # lets you run `python3 main.py` directly, using config for host/port,
    # instead of always typing the uvicorn command with explicit flags
    import uvicorn
    uvicorn.run(app, host=config.WS_HOST, port=config.WS_PORT)
