# 22-Day Roadmap

Renumbered again: 4 new days inserted for the wellness/intelligence
feature set (Days 6-9), positioned before systemd rather than after,
since the daemon's feature set should be complete before it's deployed
as a service. Everything from the old "Day 5" (systemd) onward shifted
down accordingly. History: 25 → 30 → 20 → 28 (git restart) → 17
(compressed) → 22 (this version, expanded scope for the wellness
platform pivot).

Status reflects real progress, not a fixed schedule.

## Phase 1: Local Engine & Intelligence (Days 1–9)
- [x] **Day 1** — RHEL 9 VM; Python3/pip/venv/pynput/sqlite installed, X11 confirmed; local SQLite schema (`daemon/db.py`) written and tested.
- [x] **Day 2** — Activity-tracking state machine (`daemon/tracker.py`) — idle timeout + continuous-use detection, tested with a fake clock.
- [x] **Day 3** — Real pynput listeners wired to the tracker, events logged to SQLite (`daemon/daemon.py`).
- [x] **Day 4** — FastAPI wrapper (`daemon/main.py`) with local WebSocket server (port 8000) broadcasting TRIGGER_BREAK, plus a POST endpoint for break outcomes.
- [x] **Day 5** — Production-readiness refactor: centralized config (`config.py`, `.env`), real logging, `device_id`-aware schema.
- [x] **Day 6** — `sessions` table; `tracker.py` gains `snooze_break()` (grace-period suppression, does NOT reset the streak) and an `on_session_end` callback; `/break-outcome` now correctly distinguishes a real break from a snooze.
- [x] **Day 7** — Digital Wellness Score (explainable, `wellness.py`) + Fatigue Risk Indicator (Low/Moderate/High) + Daily Wellness Goal, exposed via `GET /wellness/today`.
- [x] **Day 8** — Analytics (`analytics.py`: session stats, daily trend), Health Timeline (merges events + healthy sessions), Weekly/Monthly Reports, CSV/JSON export — all exposed via new endpoints.
- [ ] **Day 9** — Adaptive (heuristic) reminder intervals + Configurable Wellness Profiles + Categorized Smart Suggestions

## Phase 2: Linux Deployment (Day 10)
- [ ] **Day 10** — `ergomonitor.service` systemd unit; boot/restart/background testing

## Phase 3: AWS Cloud Integration (Days 11–16)
- [ ] **Day 11** — RDS PostgreSQL instance + IAM roles
- [ ] **Day 12** — Sync script: local SQLite → RDS (now including sessions + wellness data), 24h/shutdown trigger, offline retry
- [ ] **Day 13** — API Gateway + Lambda (historical data endpoint)
- [ ] **Day 14** — Cognito, part 1: user pool + app client setup
- [ ] **Day 15** — Cognito, part 2: integration + testing (kept at 2 days — flagged weak spot)

## Phase 4: React Dashboard (Days 16–19)
- [ ] **Day 16** — React app init + layout + Cognito login flow
- [ ] **Day 17** — WebSocket integration with the local daemon + wellness score/analytics display
- [ ] **Day 18** — Full-screen intervention overlay + categorized suggestion display
- [ ] **Day 19** — Integration testing across local + cloud + UI

## Phase 5: Polish & Documentation (Days 20–22)
- [ ] **Day 20** — Graceful failure testing (offline scenarios) + UI/UX polish
- [ ] **Day 21** — Architecture diagrams + documentation
- [ ] **Day 22** — Final presentation prep
