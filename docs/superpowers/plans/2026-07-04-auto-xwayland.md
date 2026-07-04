# Auto-XWayland Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect Wayland sessions and auto-relaunch DuckStation under XWayland if it is running under native Wayland.

**Architecture:** Add a `_ensure_xwayland()` helper function in `xeupiu.py` that runs before `App()` is constructed. On X11 or when DuckStation is already on XWayland, it is a no-op. On Wayland with DuckStation running natively, it shows a confirm dialog offering to relaunch the process under the XWayland env vars.

**Tech Stack:** Python 3.11, tkinter (existing), stdlib subprocess/os/signal. No new dependencies.

## Global Constraints

- Python >= 3.11 (from pyproject.toml)
- Linux-only code path (guarded by `sys.platform == "linux"` and `WAYLAND_DISPLAY` env check)
- No new dependencies (stdlib subprocess, os, signal, tkinter only)
- YAGNI: no config flags, no kill-switch, no `duckstation_cmd` override. Hardcode correct behavior.
- No test suite exists in this project; verification is manual (see Task 1 verification steps)

---

### Task 1: Add Wayland detection and relaunch to xeupiu.py

**Files:**
- Modify: `src/xeupiu/xeupiu.py:1-14` (imports)
- Modify: `src/xeupiu/xeupiu.py:177-183` (save_and_run)
- Add after line 14: all new functions (~60 LOC)

**Interfaces:**
- `_ensure_xwayland() -> bool` — returns True to proceed, False to abort

- [ ] **Step 1: Add imports**

Add `subprocess`, `os`, `signal` to the import block at the top of `xeupiu.py`. Place them after the existing `import time` line (line 8).

```python
import argparse
import os
import pathlib
import signal
import subprocess
import tkinter as tk
from tkinter import scrolledtext, ttk
import sys
import time
```

- [ ] **Step 2: Write _find_duckstation_pids()**

Add this function after the imports, before the `StdoutRedirector` class (after line 14).

```python
def _find_duckstation_pids():
    """Return list of (pid_str, cmdline_str) tuples for running DuckStation processes."""
    try:
        result = subprocess.run(
            ["pgrep", "-af", CONFIG["window_title"]],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return []
        pids = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                pids.append((parts[0], parts[1]))
        return pids
    except Exception:
        return []
```

- [ ] **Step 3: Write _show_xwayland_dialog()**

Add this function directly after `_find_duckstation_pids()`.

```python
def _show_xwayland_dialog(command, pids):
    """Show 3-button dialog. Returns True if relaunched, False otherwise."""
    result = [None]

    dlg = tk.Toplevel()
    dlg.title("XWayland Required")
    dlg.transient()
    dlg.grab_set()
    dlg.resizable(False, False)

    tk.Label(
        dlg,
        text="DuckStation is running under native Wayland.\n"
             "XEUPIU needs it on XWayland to capture screenshots.",
        wraplength=400,
        justify="left",
        padx=12,
        pady=(12, 0),
    ).pack()

    tk.Label(
        dlg,
        text=command,
        wraplength=400,
        justify="left",
        padx=12,
        pady=(6, 0),
        fg="#666",
    ).pack()

    btn_frame = tk.Frame(dlg, padx=12, pady=12)
    btn_frame.pack(fill="x")

    def on_relaunch():
        result[0] = "relaunch"
        dlg.destroy()

    def on_copy():
        result[0] = "copy"
        dlg.destroy()

    def on_cancel():
        result[0] = "cancel"
        dlg.destroy()

    tk.Button(btn_frame, text="Relaunch", command=on_relaunch, width=12).pack(side="left", padx=(0, 4))
    tk.Button(btn_frame, text="Copy command", command=on_copy, width=14).pack(side="left", padx=4)
    tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side="right")

    dlg.wait_window()

    if result[0] == "relaunch":
        return _relaunch_duckstation(pids)
    elif result[0] == "copy":
        try:
            root = tk._default_root
            if root:
                root.clipboard_clear()
                root.clipboard_append(command)
        except Exception:
            pass
        print(f"Copied to clipboard. To relaunch DuckStation:\n  {command}")
    return False
```

- [ ] **Step 4: Write _relaunch_duckstation()**

Add this function directly after `_show_xwayland_dialog()`.

```python
def _relaunch_duckstation(pids):
    """Kill DuckStation processes, respawn with XWayland env vars. Returns True if window appears."""
    for pid_str, _ in pids:
        try:
            os.kill(int(pid_str), signal.SIGTERM)
        except (ProcessLookupError, PermissionError, ValueError):
            pass

    time.sleep(1)

    for _, cmdline in pids:
        try:
            parts = cmdline.split()
            subprocess.Popen(
                ["env", "-u", "WAYLAND_DISPLAY", "QT_QPA_PLATFORM=xcb"] + parts,
                start_new_session=True,
            )
            break
        except Exception as e:
            print(f"Failed to relaunch DuckStation: {e}")
            return False

    for _ in range(40):
        time.sleep(0.25)
        try:
            get_window_by_title(CONFIG["window_title"])
            print("DuckStation relaunched under XWayland.")
            return True
        except ValueError:
            continue

    print("Error: DuckStation did not reappear on XWayland within 10 seconds.")
    return False
```

- [ ] **Step 5: Write _ensure_xwayland()**

Add this function directly after `_relaunch_duckstation()`.

```python
def _ensure_xwayland():
    """Check Wayland + DuckStation state. Show dialog if needed. Returns True to proceed, False to abort."""
    if sys.platform != "linux":
        return True
    if not os.environ.get("WAYLAND_DISPLAY"):
        return True

    try:
        get_window_by_title(CONFIG["window_title"])
        return True
    except ValueError:
        pass

    pids = _find_duckstation_pids()
    if not pids:
        return True

    original_cmd = pids[0][1]
    xwayland_cmd = f"env -u WAYLAND_DISPLAY QT_QPA_PLATFORM=xcb {original_cmd}"
    return _show_xwayland_dialog(xwayland_cmd, pids)
```

- [ ] **Step 6: Wire into save_and_run()**

Replace lines 177-183 of `xeupiu.py`. The new code inserts the XWayland check between `update_idletasks()` and `App()`.

**Before (lines 177-183):**
```python
    def save_and_run(self):
        # creating the app causes a small pause because it loads the database files.
        # print a message to the terminal and update all the widgets so that users see
        # that we're doing something.
        print("Loading...", flush=True)
        self.root.update_idletasks()
        self.app = App()
```

**After:**
```python
    def save_and_run(self):
        # creating the app causes a small pause because it loads the database files.
        # print a message to the terminal and update all the widgets so that users see
        # that we're doing something.
        print("Loading...", flush=True)
        self.root.update_idletasks()

        if not _ensure_xwayland():
            print("Aborted. Fix DuckStation's launch environment and try again.")
            return

        self.app = App()
```

- [ ] **Step 7: Manual verification on Wayland**

On Bazzite/KDE Plasma session, with DuckStation running under native Wayland:
1. Run `xeupiu` from terminal
2. Expected: dialog appears with DuckStation's cmdline
3. Click "Relaunch" — DuckStation closes, relaunches, XEUPIU continues loading
4. Click "Cancel" — dialog closes, XEUPIU prints abort message and returns to idle

- [ ] **Step 8: Manual verification on X11**

On any Linux X11 session (or XWayland session where DuckStation is already on XWayland):
1. Run `xeupiu` from terminal
2. Expected: no dialog, normal "Loading..." behavior, app works as before

- [ ] **Step 9: Commit**

```bash
git add src/xeupiu/xeupiu.py
git commit -m "feat: auto-relaunch DuckStation under XWayland for Wayland users

Detects native-Wayland DuckStation at startup via pgrep. Shows a
3-button dialog (Relaunch / Copy / Cancel) with the relaunch command.
On confirm: kills the process, respawns with WAYLAND_DISPLAY removed
and QT_QPA_PLATFORM=xcb, polls for XWayland window reappear.

On X11 or when DuckStation is already on XWayland, the check is a
no-op. No new deps (stdlib subprocess/os/signal + existing tkinter)."
```
