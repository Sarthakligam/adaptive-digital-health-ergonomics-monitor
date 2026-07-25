# Environment Setup / Recovery

Use this if you're ever rebuilding the dev environment on a different
machine (laptop lost/unavailable, fresh install, etc.) instead of
restoring the VMware VM backup. This is the command-only version of
Days 1-3 — see git history / VIVA_PREP.md for the full explanations.

## 1. RHEL 9 VM
- Install VMware Workstation Player (free) or Pro.
- Create a new VM, attach a RHEL 9 ISO.
- During install: enable networking, create an admin user, choose
  **"Server with GUI"** as the software selection (not Minimal/headless —
  the daemon needs a desktop session for pynput and the overlay).
- After first boot: `sudo dnf install open-vm-tools open-vm-tools-desktop -y && sudo reboot`
  (clipboard sharing + display integration with the host).

## 2. Python environment
```bash
sudo dnf install python3-pip sqlite git -y
git clone <your-repo-url> ~/adhem
cd ~/adhem
python3 -m venv venv
source venv/bin/activate
pip install pynput fastapi uvicorn websockets
```

## 3. Confirm session type (pynput needs X11, not Wayland)
```bash
echo $XDG_SESSION_TYPE
```
If `wayland`: log out → gear icon on login screen → **"GNOME on Xorg"** → log back in.

## 4. Verify the daemon pieces work
```bash
cd ~/adhem/daemon
python3 test_tracker.py   # 6x PASS expected
python3 test_daemon.py    # 3x PASS expected
python3 db.py             # "Database ready at ..."
```

## 5. Re-clone and go
Once the above passes, you're back to exactly where this laptop's
setup stood — continue from whatever Day the roadmap shows as the
last completed one.
