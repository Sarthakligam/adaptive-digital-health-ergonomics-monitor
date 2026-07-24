# 28-Day Roadmap

Renumbered after the git repo was restarted: the original setup work
(RHEL VM, Python/pynput install, SQLite schema — originally Days 1-3)
is now squashed into a single Day 1, already committed and pushed.
Everything from there keeps the original day-by-day pacing, just
shifted down by 2 (old Day 4 → new Day 2, ... old Day 30 → new Day 28).

Status reflects real progress, not a fixed schedule.

## Phase 1: Local Engine & Linux Deployment (Days 1–7)
- [x] **Day 1** — RHEL 9 VM (VMware Workstation 17 Pro); Python3/pip/venv/pynput/sqlite installed, X11 session confirmed; local SQLite schema (`daemon/db.py`) written and tested. Squashed into one commit, already pushed.
- [ ] **Day 2** — Core daemon, part 1: activity-tracking state machine (idle timeout + continuous-use detection)
- [ ] **Day 3** — Core daemon, part 2: wire up real pynput listeners + SQLite event logging
- [ ] **Day 4** — Daemon testing & refinement
- [ ] **Day 5** — FastAPI wrapper + local WebSocket server (port 8000)
- [ ] **Day 6** — `ergomonitor.service` systemd unit
- [ ] **Day 7** — systemd boot/restart/background testing

## Phase 2: AWS Cloud Integration (Days 8–15)
- [ ] **Day 8** — RDS PostgreSQL instance
- [ ] **Day 9** — IAM roles
- [ ] **Day 10** — Sync script, part 1: read local SQLite, push to RDS
- [ ] **Day 11** — Sync script, part 2: 24h/shutdown trigger + offline retry
- [ ] **Day 12** — API Gateway + Lambda (historical data endpoint)
- [ ] **Day 13** — Cognito, part 1: user pool setup
- [ ] **Day 14** — Cognito, part 2: integration
- [ ] **Day 15** — Cognito, part 3: testing (kept as 3 days — flagged weak spot)

## Phase 3: React Dashboard (Days 16–22)
- [ ] **Day 16** — React app init + layout
- [ ] **Day 17** — Cognito login flow integration
- [ ] **Day 18** — WebSocket integration with the local daemon
- [ ] **Day 19** — Cloud data fetch + charts
- [ ] **Day 20** — Full-screen intervention overlay, part 1 (note: true "always on top" needs a desktop shell like Electron — a browser tab can't force itself above other apps; we'll settle this when we get there)
- [ ] **Day 21** — Full-screen intervention overlay, part 2
- [ ] **Day 22** — Integration testing across local + cloud + UI

## Phase 4: Polish & Documentation (Days 23–28)
- [ ] **Day 23** — Graceful failure testing (offline scenarios)
- [ ] **Day 24** — UI/UX polish, part 1
- [ ] **Day 25** — UI/UX polish, part 2
- [ ] **Day 26** — Architecture diagrams
- [ ] **Day 27** — Documentation / report writing
- [ ] **Day 28** — Final presentation prep
