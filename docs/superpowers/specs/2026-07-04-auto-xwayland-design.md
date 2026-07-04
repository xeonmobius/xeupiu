# Auto-XWayland Support Design

**Date:** 2026-07-04
**Status:** Approved
**Scope:** Make XEUPIU work on Wayland-native Linux distros (Bazzite, Fedora, etc.) without manual env-var setup.

## Problem

XEUPIU's Linux screenshot module (`src/xeupiu/linux/screenshot.py`) uses `ewmhlib` + `Xlib` to enumerate the X client list and grab the DuckStation window's buffer. On Wayland compositors (Bazzite/KDE Plasma, GNOME, wlroots), DuckStation runs as a **native Wayland client by default** and never appears in the XWayland client list — so `get_window_by_title()` fails and the tool cannot start.

The deeper blocker: Wayland has **no global coordinate space**. Even with a screenshot, an app cannot read another window's absolute position. XEUPIU's `OverlayWindow` (`src/xeupiu/overlay.py:88-102`) positions itself using absolute screen coordinates from `get_window_base_dims()`. Native Wayland capture via `xdg-desktop-portal` + PipeWire would not restore this — it would require redesigning the overlay into a fullscreen borderless layer with manual/region-based alignment, which degrades the product.

The current workaround (`tutorial.md:22-27`) requires the user to manually launch DuckStation with:
```
env -u WAYLAND_DISPLAY QT_QPA_PLATFORM=xcb <duckstation>
```
This is error-prone and undocumented for new Bazzite users.

## Decision

**Auto-XWayland.** Detect Wayland at startup. If DuckStation is running under native Wayland, offer to relaunch it under XWayland automatically. Keep all existing X11 screenshot and overlay code unchanged.

### Why not native Wayland

| Factor | XWayland | Native Wayland (portal+PipeWire) |
|---|---|---|
| Compatibility | Universal (shipped by all Linux distros) | Requires portal backend + PipeWire + correct KDE/GNOME/wlr impl |
| Performance | Direct X buffer grab (~1ms) | Video stream overhead + dbus setup latency |
| Window positioning | Works (absolute coords) → overlay aligns | Broken (no global coords) → overlay redesign required |
| User friction | One-time relaunch dialog | Permission dialog every launch |
| New deps | None | dbus-python, python-pipewire / gstreamer |
| Code paths | Zero new | ~300+ LOC new module |

XWayland exists precisely for apps like this one (read other windows + position precisely over them). Forcing DuckStation into XWayland preserves the overlay positioning model with zero compromises.

### Future-proofing

A planned "show Japanese, click to reveal English" learning feature does not change this decision. If that feature lives in the control panel (side list + click-to-reveal popup), it is platform-agnostic. If it lives as a game overlay (click-on-textbox to flip JP↔EN), it requires absolute positioning → XWayland-only by definition. Either path keeps XWayland correct.

## Design

### Detection (called from `save_and_run()` in `xeupiu.py`)

Before `self.app = App()` is constructed, run a Wayland check:

1. If `sys.platform != "linux"` → skip (Windows path unchanged).
2. If `os.environ.get("WAYLAND_DISPLAY")` is unset → skip (X11 session or already pre-configured).
3. Try `get_window_by_title(CONFIG["window_title"])`:
   - **Found** → DuckStation already on XWayland → proceed normally. Zero behavior change.
   - **Not found** → step 4.
4. Detect DuckStation process via `subprocess.run(["pgrep", "-af", "duckstation"])`:
   - **No match** → DuckStation is not running. Proceed to `App()`; the existing "window not found" error path handles it.
   - **Match(es)** → DuckStation is running but not in the X client list → native Wayland problem → trigger relaunch flow.

### Relaunch flow (confirm dialog + relaunch button)

Show a custom `tk.Toplevel` dialog (tk's stock `messagebox` maxes out at two buttons; we need three) containing:

- Explanation: "DuckStation is running under native Wayland. The overlay needs XWayland."
- The exact command that will be run: `env -u WAYLAND_DISPLAY QT_QPA_PLATFORM=xcb <original cmdline>`
- Three buttons: **Relaunch**, **Copy command**, **Cancel**

**Relaunch action:**
1. Parse the first PID + full cmdline from `pgrep -af` output. Output format is `"<PID> <cmdline...>\n"` per line — split on first space, first token is PID (int), remainder is the full cmdline string. Use the first matching line.
2. Send `SIGTERM` to the DuckStation PID(s) via `os.kill(pid, signal.SIGTERM)`.
3. Re-spawn via `subprocess.Popen(["env", "-u", "WAYLAND_DISPLAY", "QT_QPA_PLATFORM=xcb", *original_cmdline])`. The original cmdline is preserved verbatim so AppImage paths, ROM arguments, and flags survive.
4. Poll `get_window_by_title()` for up to 10 seconds (e.g. 40 tries × 250 ms) waiting for the XWayland window to appear.
5. **Success** → proceed to `App()`.
6. **Timeout** → show error: "DuckStation did not reappear on XWayland within 10 s. Check the command and relaunch manually." Abort.

**Copy command action:** Copy the full env-var command to the clipboard (via tkinter clipboard), abort the run, let the user relaunch DuckStation manually.

**Cancel action:** Abort the run.

### Code changes

| File | Change |
|---|---|
| `src/xeupiu/xeupiu.py` | Add `_ensure_xwayland()` helper (~60 LOC). Call it at the top of `save_and_run()` before `self.app = App()`. Return early (abort run) if it returns `False`. |

No other files change. Specifically:

- `src/xeupiu/linux/screenshot.py` — untouched
- `src/xeupiu/screenshot.py` — untouched
- `src/xeupiu/overlay.py` — untouched
- `pyproject.toml` — no new deps (stdlib `subprocess`, `os`, `signal`; `pgrep` is universal on Linux)
- `config.json` / `config_generic.json` — no new flags (YAGNI; behavior is correct-by-default)

### Dependencies

None new. Detection uses stdlib only:

- `subprocess` — `pgrep` invocation, `Popen` relaunch
- `os` — env-var check, `os.kill`
- `signal` — `SIGTERM`
- `tkinter.messagebox` — confirm dialog (tkinter already a transitive dependency via the GUI)

### Edge cases

- **Steam-launched DuckStation.** The respawn is a standalone process; Steam will mark the game as closed. This is an acceptable tradeoff. The dialog footnotes this behavior so the user is not surprised.
- **Multiple DuckStation processes** (unlikely). All matching PIDs are terminated; the first cmdline found is used for respawn.
- **Permission denied on kill.** Same-user process, should not occur. If `os.kill` raises, catch and show error.
- **Respawn fails** (e.g. binary moved). `Popen` raises → catch → show error with the failed command.
- **`WAYLAND_DISPLAY` already unset by user.** Detection step 2 skips the whole check → no dialog, no-op. Backward-compatible with the documented manual workaround.
- **DuckStation launched via wrapper script.** The respawn reuses the exact cmdline from `pgrep -af`, which captures the wrapper invocation, not just the binary. Behavior is preserved.

### What does NOT change

- `linux/screenshot.py` — X11 code stays exactly as is.
- Overlay positioning — works because XWayland provides absolute window coordinates.
- Windows code path — untouched.
- Existing tutorial workaround — still valid and still documented; just no longer required for the common case.

## Non-goals (YAGNI)

- Native Wayland screenshot capture via xdg-desktop-portal / PipeWire.
- Overlay redesign for coordinate-free positioning.
- `grim` / `slurp` external-tool capture.
- Config flags to disable the autorelaunch (deferred until a user actually needs a kill-switch).
- A `duckstation_cmd` config override (autodetection from `pgrep` is sufficient).
- `psutil` dependency (stdlib `subprocess` + `pgrep` covers the Linux-only use case).

## Verification

Manual, since the project has no test suite:

1. On a Bazzite/KDE Plasma session, launch DuckStation normally (native Wayland).
2. Launch XEUPIU, click "Save and run".
3. Confirm the relaunch dialog appears with the correct detected cmdline.
4. Click "Relaunch" → DuckStation should reappear under XWayland and XEUPIU proceeds to the overlay.
5. Click "Copy command" → clipboard contains the env-var command, run aborts cleanly.
6. Click "Cancel" → run aborts cleanly, no DuckStation touched.
7. Pre-launch DuckStation with the manual env vars → no dialog should appear (detection step 3 succeeds).
8. On an X11 session (`WAYLAND_DISPLAY` unset) → no dialog, behavior unchanged from today.
