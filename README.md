# Adaptive Digital Health & Ergonomics Monitor

A hybrid local/cloud system that tracks keyboard and mouse *activity*
(never key content — booleans only) on a RHEL 9 Linux daemon, triggers
ergonomic break reminders after sustained continuous use, syncs daily
summaries to AWS, and visualizes history through a React dashboard.

Day-count history: scoped as a 25-day build, expanded to 30 for buffer
room, briefly compressed to 20, restarted at 28 after folding initial
setup into one Day 1 commit, and compressed again to the current
**17 days** once real consolidation was possible. See
[`docs/ROADMAP.md`](docs/ROADMAP.md) for the day-by-day plan and
current progress, [`docs/VIVA_PREP.md`](docs/VIVA_PREP.md) for
exam-prep questions, and [`docs/SETUP.md`](docs/SETUP.md) for a
from-scratch environment rebuild if you're ever on a different machine.

## Architecture

```
Local Machine (RHEL 9)
  Python Daemon (systemd) <--WebSocket--> React Frontend
         |                                      |
    Local SQLite                          Auth Request
         |                                      v
   Data Sync (24h/shutdown)               AWS Cognito
         v                                      |
                  AWS Cloud                  Tokens
         RDS Database <--- API Gateway & Lambda
```

## Repo layout

| Folder       | Contents                                                        |
|--------------|--------------------------------------------------------------------|
| `daemon/`    | Python tracking daemon (`tracker.py`, `daemon.py`), local SQLite schema (`db.py`), systemd unit |
| `cloud/`     | AWS sync script, Lambda function, RDS schema                        |
| `dashboard/` | React frontend                                                       |
| `docs/`      | Roadmap, viva prep, setup/recovery notes, architecture diagrams        |
| `scripts/`   | Dev tooling (optional — not currently used; commits are manual)       |

## Daily progress log

Progress is tracked via git history — one commit (and push) per work
session, labeled by day number. See `docs/ROADMAP.md` for what each
day covers and current status.
