# Viva Prep — Adaptive Digital Health & Ergonomics Monitor

Running set of likely questions per day (renumbered to match the
current 28-day roadmap). Answers below are the core idea to
internalize — say them in your own words in the actual viva, not
verbatim, so follow-up questions don't trip you up.

---

## Day 1 — Environment Setup (RHEL 9 VM, Python/pynput, SQLite Schema)

**Q: Why RHEL specifically, rather than something like Ubuntu?**
RHEL is a widely-used enterprise Linux distribution, so building on it
demonstrates familiarity with an industry-standard OS rather than a
hobbyist distro — relevant since this project is framed around
production-style deployment (systemd service, cloud integration).

**Q: Why "Server with GUI" instead of a headless/minimal install?**
The daemon needs an active desktop session for two reasons: pynput's
input-capture backend requires X11 to be running, and the break
overlay needs an actual screen to display on. A headless install has
neither.

**Q: What kind of hypervisor is VMware Workstation, and how does that differ from something like VMware ESXi?**
Workstation is a Type 2 (hosted) hypervisor — it runs on top of a host
OS (Windows here). ESXi is Type 1 (bare-metal) — it runs directly on
hardware with no host OS underneath.

**Q: Why track activity as booleans instead of logging actual keystrokes?**
Privacy by design. The goal is only to detect *presence or absence* of
activity for ergonomic timing — not to know what's being typed. Logging
real key content would make this a keylogger, which is neither
necessary for the goal nor appropriate to build.

**Q: What is a Python virtual environment and why use one here?**
An isolated set of installed packages scoped to this project, so
pynput and its dependencies don't conflict with the system Python or
with other projects on the same machine.

**Q: Why does pynput need an X11 session — what's the actual issue with Wayland?**
Wayland's security model deliberately restricts apps from globally
hooking keyboard/mouse events system-wide, precisely to prevent the
kind of surveillance a keylogger would do. X11 traditionally allows
this. pynput's Linux backend is built on X11/Xlib, so it needs that
session type to receive global events.

**Q: Why SQLite instead of a full database server, or just a flat file?**
SQLite is serverless and file-based — nothing to install or run as a
separate process — which fits a lightweight local daemon well, while
still giving real SQL querying that a flat file wouldn't.

**Q: What is the `synced` column for?**
It flags whether a row has already been pushed to AWS RDS. The later
sync script reads only unsynced rows, uploads them, and marks them
synced — so nothing gets duplicated or lost if the sync runs multiple
times.

**Q: Why does `events` use an auto-incrementing ID, but `daily_summary` uses the date as its primary key?**
Each event is a discrete, independent occurrence, so it needs a
surrogate key. `daily_summary` has exactly one row per calendar day by
design, so the date itself is already a natural, unique key — no
separate ID needed.

**Q: What does `conn.row_factory = sqlite3.Row` actually do?**
It makes query results behave like dictionaries (access by column
name) instead of plain tuples (access by position) — makes the code
that reads rows later more readable and less fragile if a column gets
added or reordered.

---

## Day 2 — Activity-Tracking State Machine

**Q: Why is `tracker.py` written with no pynput code in it at all?**
Separation of concerns: the state machine only needs to know "an
input event happened" and "time has passed" — it doesn't care where
those events come from. That decoupling is what makes it possible to
unit test the timing logic with a fake clock, instead of needing a
real keyboard or waiting 20 real minutes per test.

**Q: What is a "state machine" in this context?**
A system that's always in one of a small number of defined states
(here: active or idle) and moves between them only in response to
specific events (input arriving, time passing a threshold) — makes
the logic's behavior predictable and exhaustively testable.

**Q: Why track both `last_activity` and `continuous_start` instead of just one timestamp?**
They answer different questions. `last_activity` answers "has the
user gone idle?" (compared against a 5-minute gap). `continuous_start`
answers "how long has this unbroken streak of activity lasted?"
(compared against the 20-minute break threshold). Collapsing them into
one timestamp would make it impossible to detect idle-out and
continuous-use independently.

**Q: Why is there a `threading.Lock` around the state?**
Because `on_input_event()` will be called from pynput's listener
thread (Day 3), while `tick()` runs on a separate background thread.
Both read and write the same state, so without a lock, two threads
touching it at the same time could produce inconsistent results (a
race condition). The lock makes every state change atomic.

**Q: Why does `acknowledge_break()` exist instead of just letting the streak keep counting?**
Once the user has actually taken (or snoozed) a break, the 20-minute
continuous-use clock should restart — otherwise, five seconds after
dismissing the reminder, the same stale streak would immediately
re-trigger it again.

**Q: How was this tested without a real 20-minute wait or a real keyboard?**
With a fake clock — a substitute for `time.monotonic` that only
advances when the test tells it to, and a fake `on_input_event()`
caller standing in for pynput. That lets the test simulate 20+
minutes of activity in milliseconds of real time, deterministically.

---

## Day 3 — Wiring pynput to the Tracker + SQLite Logging

**Q: Why is the `pynput` import placed inside `start_listeners()` instead of at the top of `daemon.py`?**
So the logging functions (`log_event`, `on_trigger_break`, `on_go_idle`)
can be imported and unit-tested on any machine — even one without
pynput installed, or with no display at all — since the import only
actually runs when `start_listeners()` is called. This was proven
directly: the test suite imports `daemon.py` and confirms `pynput`
never even loads into memory as part of that import.

**Q: In `on_key_press(key)`, why does the code ignore the `key` argument pynput gives it?**
That argument would tell you exactly which key was pressed — but the
project's entire privacy design is to track *that* input happened, not
*what* it was. Accepting the parameter but never reading it is the
concrete proof of that design choice in the code itself.

**Q: Why is `log_event()` a separate function instead of writing SQL directly inside `on_trigger_break()`?**
Single responsibility: `on_trigger_break()` decides *when* something
noteworthy happened (that's the tracker's job), while `log_event()`
decides *how* it gets persisted (that's storage's job). Keeping them
separate is also what made it possible to test the logging logic on
its own, without needing a real 20-minute activity streak from a real
keyboard.

**Q: Why store timestamps in UTC (`datetime.now(timezone.utc)`) instead of local time?**
Once this syncs to AWS RDS, the server may be in a different region
than the laptop. UTC gives one unambiguous timestamp regardless of
time zone, avoiding bugs where "24 hours since last sync" gets
miscalculated across a time-zone or daylight-saving boundary.

**Q: Why does the daemon run the tracker's `run()` loop on a separate thread from the pynput listeners?**
pynput's listeners already run on their own background threads
internally and call back into `on_input_event()` almost instantly.
The tracker's periodic idle/continuous check (`tick()`, every 5
seconds) is a separate, ongoing job that shouldn't block or be
blocked by input events arriving — so it gets its own thread, and the
shared `Lock` inside `tracker.py` (from Day 2) is what keeps that safe.

---

## Day 4 — FastAPI + WebSocket Wrapper

**Project-specific questions**

**Q: Why is `ConnectionManager` in its own file (`ws_manager.py`) with no FastAPI import?**
Same reasoning as Day 3's deferred pynput import: it lets the trickiest
logic — broadcasting to multiple clients, cleanly dropping one that's
disconnected mid-broadcast — be unit-tested with plain fake objects,
without needing FastAPI itself installed or a real server running.

**Q: `on_trigger_break()` runs on a background thread, but the WebSocket broadcast is `async`. How do those connect safely?**
`asyncio.run_coroutine_threadsafe(coro, loop)` — it's the one safe way
to schedule a coroutine onto an event loop from a *different* thread.
Calling the coroutine directly from the tracker's thread would either
crash or silently do nothing, since that thread has no event loop of
its own running.

**Q: Why capture `main_loop` inside the `lifespan` function instead of just calling `asyncio.get_event_loop()` wherever it's needed?**
`lifespan` runs *on* the actual running event loop at startup, so
`asyncio.get_running_loop()` there is guaranteed correct. Calling it
later from the tracker's background thread would raise an error —
threads other than the one running the loop can't ask "what's the
current loop" that way, which is exactly why the reference has to be
captured once, up front, and reused.

**Q: What does the `POST /break-outcome` endpoint do, end to end?**
The React dashboard will call it when the user completes or snoozes a
break. It calls `tracker.acknowledge_break()` (resets the 20-minute
streak, from Day 2) and logs `break_completed` or `break_snoozed` to
SQLite (from Day 3) — tying today's new code directly back to the
first three days' work.

**Common interview questions (general, beyond this project)**

**Q: What is a WebSocket, and how is it different from a normal HTTP request?**
HTTP is request-response: the client asks, the server answers, the
connection typically closes. A WebSocket is a single long-lived
connection where either side can send messages at any time — needed
here because the server (daemon) must push a break alert to the
client (dashboard) without the client having to keep asking "is it
time yet?"

**Q: What is an event loop, in the context of asyncio?**
A single-threaded loop that continuously picks up and runs whichever
pending task is ready next — `await` points are where a task pauses
and lets the loop run something else instead of blocking.

**Q: Why might mixing threads and asyncio cause bugs if you're not careful?**
An asyncio event loop assumes everything touching it happens on the
same thread it's running on. Calling loop-bound code directly from a
different thread is a common source of "why did this silently do
nothing" or "why did this crash" bugs — which is exactly why
`run_coroutine_threadsafe` exists as the sanctioned bridge.

**Q: What's a health check endpoint (like `GET /`) typically used for?**
A cheap, fast endpoint an operator, load balancer, or monitoring tool
can hit to confirm the service is up and responsive, without
exercising any real business logic.
