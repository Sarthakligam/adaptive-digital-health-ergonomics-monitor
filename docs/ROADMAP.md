# 17-Day Roadmap

Compressed a second time — same total scope, genuinely fewer days
(not just relabeled), with extra room kept only on the two flagged
weak spots (daemon internals, Cognito). History: 25 (original) → 30
(expanded for buffer) → 20 (compressed) → 28 (git restart, Days 1-3
squashed into Day 1) → 17 (this version).

Status reflects real progress, not a fixed schedule.

## Phase 1: Local Engine & Linux Deployment (Days 1–5)
- [x] **Day 1** — RHEL 9 VM; Python3/pip/venv/pynput/sqlite installed, X11 confirmed; local SQLite schema (`daemon/db.py`) written and tested.
- [x] **Day 2** — Activity-tracking state machine (`daemon/tracker.py`) — idle timeout + continuous-use detection, tested with a fake clock.
- [x] **Day 3** — Real pynput listeners wired to the tracker, events logged to SQLite (`daemon/daemon.py`).
- [ ] **Day 4** — Daemon testing/refinement + FastAPI wrapper with local WebSocket server (port 8000)
- [ ] **Day 5** — `ergomonitor.service` systemd unit, including boot/restart/background testing

## Phase 2: AWS Cloud Integration (Days 6–10)
- [ ] **Day 6** — RDS PostgreSQL instance + IAM roles
- [ ] **Day 7** — Sync script: local SQLite → RDS, 24h/shutdown trigger, offline retry
- [ ] **Day 8** — API Gateway + Lambda (historical data endpoint)
- [ ] **Day 9** — Cognito, part 1: user pool + app client setup
- [ ] **Day 10** — Cognito, part 2: integration + testing (kept at 2 days — flagged weak spot)

## Phase 3: React Dashboard (Days 11–14)
- [ ] **Day 11** — React app init + layout + Cognito login flow
- [ ] **Day 12** — WebSocket integration with the local daemon + cloud data fetch/charts
- [ ] **Day 13** — Full-screen intervention overlay (note: true "always on top" needs a desktop shell like Electron — a browser tab can't force itself above other apps)
- [ ] **Day 14** — Integration testing across local + cloud + UI

## Phase 4: Polish & Documentation (Days 15–17)
- [ ] **Day 15** — Graceful failure testing (offline scenarios) + UI/UX polish
- [ ] **Day 16** — Architecture diagrams + documentation
- [ ] **Day 17** — Final presentation prep
