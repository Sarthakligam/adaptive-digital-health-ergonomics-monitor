# Adaptive Digital Health & Ergonomics Monitor

A hybrid local/cloud system that tracks keyboard and mouse *activity*
(never key content — booleans only) on a RHEL 9 Linux daemon, triggers
ergonomic break reminders after sustained continuous use, syncs daily
summaries to AWS, and visualizes history through a React dashboard.

Originally scoped as a 25-day build; restructured to 30 days — see
[`docs/ROADMAP.md`](docs/ROADMAP.md) for the full day-by-day plan and
current progress.

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

| Folder       | Contents                                                |
|--------------|----------------------------------------------------------|
| `daemon/`    | Python tracking daemon, local SQLite schema, systemd unit |
| `cloud/`     | AWS sync script, Lambda function, RDS schema              |
| `dashboard/` | React frontend                                             |
| `docs/`      | Roadmap, architecture diagrams, report material            |
| `scripts/`   | Dev tooling (see `scripts/commit-today.sh`)                 |

## Daily progress log

This project tracks real day-by-day progress via git history — run
`scripts/commit-today.sh` after each work session (see the script's
header comment for what it does and doesn't do).
