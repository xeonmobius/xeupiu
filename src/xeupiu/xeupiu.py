from __future__ import annotations

import argparse
import os
import pathlib
import shlex
import signal
import subprocess
import tkinter as tk
from tkinter import scrolledtext, ttk
import sys
import time

from xeupiu.app import App
from xeupiu.config import CONFIG
from xeupiu.error_window import display_error
from xeupiu.screenshot import get_window_by_title, get_window_image


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
            parts = shlex.split(cmdline)
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


class StdoutRedirector:
    def __init__(self, text_area):
        self.text_area = text_area
        self.original_stdout = sys.stdout
        sys.stdout = self

    def write(self, message):
        self.text_area.insert(tk.END, message)
        self.text_area.see(tk.END)

    def flush(self):
        pass

    def restore(self):
        sys.stdout = self.original_stdout

class XeupiuControlPanel:
    def __init__(self):
        self.app = None
        self.received_stop_signal = False

        # Create main window
        root = tk.Tk()
        root.title(f"XEUPIU {CONFIG['version']}")
        root.resizable(False, False)
        if sys.platform == "win32":
            root.iconbitmap("data/resources/icon.ico")
        elif sys.platform == "linux":
            img = tk.PhotoImage(file="data/resources/icon_small.png")
            root.iconphoto(True, img)
        else:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")

        window_width = 1024
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_coordinate = (screen_width // 2) - (window_width // 2)
        y_coordinate = (screen_height // 2) - (window_height // 2)
        # Set the geometry to center the window
        root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        # Create frames for left and right panels
        left_frame = tk.Frame(root, width=10)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        # left_frame.grid_columnconfigure(0, weight=1)
        # left_frame.grid_columnconfigure(1, weight=1)

        right_frame = tk.Frame(root, width=40)
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # right_frame.grid_columnconfigure(0, weight=1)
        # right_frame.grid_columnconfigure(1, weight=1)

        # Left panel - Input fields
        jp_name_var = tk.StringVar(value=CONFIG['save']['player']['jp_name'])
        jp_surname_var = tk.StringVar(value=CONFIG['save']['player']['jp_surname'])
        jp_nickname_var = tk.StringVar(value=CONFIG['save']['player']['jp_nickname'])
        en_name_var = tk.StringVar(value=CONFIG['save']['player']['en_name'])
        en_surname_var = tk.StringVar(value=CONFIG['save']['player']['en_surname'])
        en_nickname_var = tk.StringVar(value=CONFIG['save']['player']['en_nickname'])
        deepL_key_var = tk.StringVar(value=CONFIG['translation']['deepl']['api_key'])

        image = tk.PhotoImage(file="data/resources/logo.png")
        tk.Label(left_frame, image=image).grid(row=0, column=0, columnspan=2, sticky=tk.N)

        tk.Label(left_frame, text="Japanese surname:").grid(row=2, column=0, sticky=tk.W)
        self.jp_surname_entry = tk.Entry(left_frame, textvariable=jp_surname_var, state="disabled")
        self.jp_surname_entry.grid(row=2, column=1, sticky=tk.E)

        tk.Label(left_frame, text="Japanese name:").grid(row=3, column=0, sticky=tk.W)
        self.jp_name_entry = tk.Entry(left_frame, textvariable=jp_name_var, state="disabled")
        self.jp_name_entry.grid(row=3, column=1, sticky=tk.E)

        tk.Label(left_frame, text="Japanese nickname:").grid(row=4, column=0, sticky=tk.W)
        self.jp_nickname_entry = tk.Entry(left_frame, textvariable=jp_nickname_var, state="disabled")
        self.jp_nickname_entry.grid(row=4, column=1, sticky=tk.E)

        tk.Label(left_frame, text="English name:").grid(row=5, column=0, sticky=tk.W)
        self.en_name_entry = tk.Entry(left_frame, textvariable=en_name_var)
        self.en_name_entry.grid(row=5, column=1, sticky=tk.E)

        tk.Label(left_frame, text="English surname:").grid(row=6, column=0, sticky=tk.W)
        self.en_surname_entry = tk.Entry(left_frame, textvariable=en_surname_var)
        self.en_surname_entry.grid(row=6, column=1, sticky=tk.E)

        tk.Label(left_frame, text="English nickname:").grid(row=7, column=0, sticky=tk.W)
        self.en_nickname_entry = tk.Entry(left_frame, textvariable=en_nickname_var)
        self.en_nickname_entry.grid(row=7, column=1, sticky=tk.E)

        tk.Label(left_frame, text="DeepL Key:").grid(row=8, column=0, sticky=tk.W)
        self.deepL_key_entry = tk.Entry(left_frame, textvariable=deepL_key_var, show="*")
        self.deepL_key_entry.grid(row=8, column=1, sticky=tk.E)

        tk.Label(left_frame, text="Translation backend:").grid(row=9, column=0, sticky=tk.W)
        self.backend_var = tk.StringVar(value=CONFIG['translation']['backend'])
        self.backend_menu = tk.OptionMenu(left_frame, self.backend_var, "deepl", "sugoi", "openai", "google_cloud")
        self.backend_menu.grid(row=9, column=1, sticky=tk.E)

        self.launch_ds_button = tk.Button(
            left_frame,
            text="LAUNCH DUCKSTATION",
            command=self.launch_duckstation,
            width=20,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.launch_ds_button.grid(row=10, column=0, columnspan=2, pady=5, sticky="ew")
        if not CONFIG.get('duckstation_path', '').strip():
            self.launch_ds_button.config(state="disabled")

        tk.Label(left_frame, text="Verbose level:").grid(row=11, column=0, sticky=tk.W)
        self.verbose_var = tk.IntVar(value=CONFIG['verbose_level'])
        self.verbose_entry = tk.Entry(left_frame, textvariable=self.verbose_var)
        self.verbose_entry.grid(row=11, column=1, sticky=tk.E)

        tk.Label(left_frame, text="History size:").grid(row=12, column=0, sticky=tk.W)
        self.history_size_var = tk.IntVar(value=CONFIG['history_size'])
        self.history_size_entry = tk.Entry(left_frame, textvariable=self.history_size_var)
        self.history_size_entry.grid(row=12, column=1, sticky=tk.E)

        self.fullscreen_var = tk.IntVar(value=CONFIG['fullscreen'])
        self.fullscreen_checkbox = tk.Checkbutton(left_frame, text="Fullscreen", variable=self.fullscreen_var)
        self.fullscreen_checkbox.grid(row=13, column=0, columnspan=2, sticky=tk.W)

        self.run_button = tk.Button(left_frame, text="Save and run", command=self.save_and_run, width=15)
        self.run_button.grid(row=14, column=0, pady=5, sticky=tk.E)

        root.protocol("WM_DELETE_WINDOW", self.close)
        self.exit_button = tk.Button(left_frame, text="Close app", command=self.close, width=15)
        self.exit_button.grid(row=14, column=1, pady=5, padx=5, sticky=tk.W)
        self.exit_button.config(state="disabled")

        self.log_button = tk.Button(left_frame, text="(DEBUG) Log everything", command=self.log_everything)
        self.log_button.grid(row=15, column=0, columnspan=2, pady=5)

        separator = ttk.Separator(left_frame, orient="horizontal")
        separator.grid(row=16, columnspan=2, pady=10, sticky="ew")

        notes_label = tk.Label(left_frame, text="NOTES:", font=("Arial", 10, "bold"))
        notes_label.grid(row=17, column=0, columnspan=2, sticky=tk.W)

        notes_text = tk.Label(left_frame, text='1. When creating your save, please make sure to input the japanese '
                                               'name, surname, and nickname displayed above. This will guarantee that '
                                               'the tool is able to detect them correctly. Fill the English fields '
                                               'with your desired names you want to use in the game.\n\n'
                                               '2. At the current phase of the project, a valid DeepL Key is required '
                                               'for the translation of the game. Please make sure to input a valid key '
                                               '-- the free ones are more than enough to play through the game multiple '
                                               'times. Visit the DeepL website for more information.\n\n'
                                               '3. If you encounter any problems, please read the FAQ in the ' 
                                               'XEUPIU GitHub repository.\n\n'
                                               '4. Enjoy the game!',
                              wraplength=0.3*window_width, justify=tk.LEFT)
        notes_text.grid(row=16, column=0, columnspan=2, sticky=tk.W)

        separator = ttk.Separator(left_frame, orient="horizontal")
        separator.grid(row=17, columnspan=2, pady=10, sticky="ew")

        notes_label = tk.Label(left_frame, text=f"XEUPIU {CONFIG['version']}\n"
                                                f"typed in brazil by vinizinho, 2024", font=("Courier", 10, "italic"))
        notes_label.grid(row=18, column=0, columnspan=2, sticky=tk.N)

        # Right panel - Text area
        self.output_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, bg="black", height=50,
                                                     fg="white", font=("MS Gothic", 12))
        self.output_text.pack()

        # Redirect stdout to the text area
        stdout_redirector = StdoutRedirector(self.output_text)

        # Start main loop
        self.root = root
        root.mainloop()

        # Restore original stdout
        stdout_redirector.restore()

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

        CONFIG['save']['player']['en_name'] = self.en_name_entry.get()
        CONFIG['save']['player']['en_surname'] = self.en_surname_entry.get()
        CONFIG['save']['player']['en_nickname'] = self.en_nickname_entry.get()
        CONFIG['fullscreen'] = bool(self.fullscreen_var.get())
        CONFIG['verbose_level'] = self.verbose_var.get()
        CONFIG['history_size'] = self.history_size_var.get()
        CONFIG['translation']['deepl']['api_key'] = self.deepL_key_entry.get()
        CONFIG['translation']['backend'] = self.backend_var.get()

        CONFIG.save()

        self.jp_name_entry.config(state="disabled")
        self.jp_surname_entry.config(state="disabled")
        self.jp_nickname_entry.config(state="disabled")
        self.en_name_entry.config(state="disabled")
        self.en_surname_entry.config(state="disabled")
        self.en_nickname_entry.config(state="disabled")
        self.deepL_key_entry.config(state="disabled")
        self.verbose_entry.config(state="disabled")
        self.history_size_entry.config(state="disabled")
        self.fullscreen_checkbox.config(state="disabled")
        self.run_button.config(state="disabled")
        self.exit_button.config(state="active")

        if self.deepL_key_entry.get() == "":
            display_error("Project XEUPIU - Error!", "DeepL key is not set. If any novel text is encountered, it will remain untranslated.")

        # there's a lot of overlays, let their rendering do their initial update before
        # we start working (in particular, setting attributes like the alpha are idle
        # events that don't process immediately)
        self.root.after_idle(self.root.after, 0, self._step)

    def launch_duckstation(self):
        """Launch DuckStation with XWayland env vars."""
        path = CONFIG.get('duckstation_path', '').strip()
        if not path:
            display_error(
                "DuckStation Path Not Set",
                "Set the DuckStation executable path in config.json first.\n"
                "Edit config.json: \"duckstation_path\": \"/path/to/duckstation\""
            )
            return

        try:
            parts = shlex.split(path)
            subprocess.Popen(
                ["env", "-u", "WAYLAND_DISPLAY", "QT_QPA_PLATFORM=xcb"] + parts,
                start_new_session=True,
            )
            print(f"Launched DuckStation: {path}")
        except Exception as e:
            display_error("Launch Failed", f"Failed to launch DuckStation:\n{e}")

    def _step(self):
        assert self.app is not None
        try:
            tik = time.monotonic_ns()
            self.app.step()
            tok = time.monotonic_ns()
            step_time_ns = tok - tik
            step_time_ms = int(step_time_ns / 1000000)
            fpms = int(1/30 * 1000)
            # setting to sleep time of 1 allows tk to generate/process non-idle events
            # like button clicks
            wait_time = max(fpms - step_time_ms, 0)
            # if not stopping, reschedule this function in the event loop
            if not self.received_stop_signal:
                # finish rendering, and *then* schedule ourselves for the future
                self.root.after_idle(self.root.after, wait_time, self._step)
        except Exception as e:
            self.app.handle_error(e)
            raise e from None

    def close(self):
        print("Exiting...")
        self.received_stop_signal = True
        self.root.destroy()

    def log_everything(self):
        print_history = self.output_text.get("1.0", 'end-1c')
        if self.app is not None:
            self.app.log_everything(print_history=print_history)

def main():
    parser = argparse.ArgumentParser(description="Tokimeki memorial translation tool.")
    parser.add_argument("--screenshot", type=pathlib.Path, help="Save a screenshot of the current game window, for debugging.")
    args = parser.parse_args()
    
    # take a screenshot and exit
    if args.screenshot is not None:
        if args.screenshot.is_dir():
            parser.error("Path to save screenshot is a directory, must be a file")
        window_id = get_window_by_title("Tokimeki Memorial")
        window_pixels = get_window_image(window_id)
        if window_pixels:
            window_pixels.save(args.screenshot)

    # run xeupiu as normal
    else:
        xcp = XeupiuControlPanel()

if __name__ == "__main__":
    main()
