# 20-Day Roadmap

Compressed from the original 30-day version — same total scope, fewer
calendar days, more packed into each one. (History: started as a
25-day plan, expanded to 30 for buffer room, now compressed to 20.)

Status reflects real progress, not a fixed schedule — update the
checkboxes as work actually happens.

## Phase 1: Local Engine & Linux Deployment (Days 1–6)
- [x] **Day 1** — RHEL 9 VM running (VMware Workstation 17 Pro)
- [x] **Day 2** — Python3, pip, venv, pynput, sqlite installed; X11 session confirmed
- [x] **Day 3** — Local SQLite schema (`daemon/db.py`) — written, tested, verified
- [ ] **Day 4** — Core daemon: pynput hooks feeding an idle/continuous-use state machine, plus testing it
- [ ] **Day 5** — FastAPI wrapper + local WebSocket server (port 8000)
- [ ] **Day 6** — `ergomonitor.service` systemd unit; boot/restart/background testing

## Phase 2: AWS Cloud Integration (Days 7–11)
- [ ] **Day 7** — RDS PostgreSQL instance + IAM roles
- [ ] **Day 8** — Sync script (local SQLite → RDS, 24h/shutdown trigger, offline retry)
- [ ] **Day 9** — API Gateway + Lambda (historical data endpoint)
- [ ] **Day 10–11** — Cognito user pool + integration (kept at 2 days — still your flagged weak spot)

## Phase 3: React Dashboard (Days 12–16)
- [ ] **Day 12** — React app init, layout, Cognito login flow
- [ ] **Day 13** — WebSocket integration with the local daemon
- [ ] **Day 14** — Cloud data fetch + charts
- [ ] **Day 15** — Full-screen intervention overlay (note: true "always on top" needs a desktop shell like Electron — a browser tab can't force itself above other apps; we'll settle this when we get there)
- [ ] **Day 16** — Integration testing across local + cloud + UI

## Phase 4: Polish & Documentation (Days 17–20)
- [ ] **Day 17** — Graceful failure testing (offline scenarios)
- [ ] **Day 18** — UI/UX polish
- [ ] **Day 19** — Architecture diagrams + documentation
- [ ] **Day 20** — Final presentation prep
