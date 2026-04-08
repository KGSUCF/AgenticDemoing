"""
Gertrude Shell - Main tkinter Application (gertrude_shell.py)
=============================================================
Prototype 1 of 3 - Windows accessibility shell for Gertrude (age 103).

Run with:
    python gertrude_shell.py

Requirements:
    Python 3.8+, tkinter (built-in), Pillow (pip install Pillow)

Compatibility:
    Windows 7, 8, 10, 11
"""

import sys
import os
import subprocess
import platform
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from typing import Optional

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import shell_logic

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CONFIG_PATH = os.path.join(_HERE, "config.json")
PHOTOS_DIR  = os.path.join(_HERE, "photos")

# Persistent Chrome profile — keeps Gertrude logged in between sessions
if platform.system() == "Windows":
    _APPDATA    = os.environ.get("APPDATA", os.path.expanduser("~"))
    PROFILE_DIR = os.path.join(_APPDATA, "GertrudeShell", "ChromeProfile")
else:
    PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".gertrude_shell", "chrome_profile")

CHROME_PATHS_WINDOWS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

ALL_APPS = [
    {
        "key":   "facebook",
        "label": "Facebook",
        "url":   "https://www.facebook.com",
        "color": "#1877F2",
        "fg":    "#FFFFFF",
    },
    {
        "key":   "milo",
        "label": "Milo\n(Google Photos)",
        "url":   "https://photos.google.com/share/AF1QipNJPdaXpqnpWA4lwzgMgta8gjcUI3OORBzlSv9Ny9QHVte3s4c16CSE8GHf0pNssw?key=TTBGSzR5QU0xblJXR3hQY05JNnBMNDNxUmhHWGxn",
        "color": "#34A853",
        "fg":    "#FFFFFF",
    },
    {
        "key":   "aol_news",
        "label": "AOL News",
        "url":   "https://www.aol.com",
        "color": "#FF0000",
        "fg":    "#FFFFFF",
    },
    {
        "key":   "aol_mail",
        "label": "AOL Mail",
        "url":   "https://mail.aol.com",
        "color": "#FF6600",
        "fg":    "#FFFFFF",
    },
]

# ---------------------------------------------------------------------------
# Colours and fonts
# ---------------------------------------------------------------------------
BG_MAIN        = "#FFF8F0"
BG_BOARD       = "#FFF3E0"
BG_BEVEL_OUTER = "#C8A97A"
BG_BEVEL_INNER = "#E8D5B7"

FG_TITLE       = "#4A2C0A"
FG_GREETING    = "#6B3A10"
FG_PHOTO_LABEL = "#FFFFFF"

FONT_TITLE    = ("Segoe UI", 24, "bold")
FONT_GREETING = ("Segoe UI", 20)
FONT_BUTTON   = ("Segoe UI", 16, "bold")
FONT_PHOTO    = ("Segoe UI", 14, "bold")
FONT_END      = ("Segoe UI", 13, "bold")
FONT_SETUP    = ("Segoe UI", 13)

GREETING_REFRESH_MS = 60_000
BANNER_H = 220          # Height of the floating banner strip in pixels


# ---------------------------------------------------------------------------
# Helper: find Chrome
# ---------------------------------------------------------------------------

def find_chrome() -> Optional[str]:
    if platform.system() == "Windows":
        for path in CHROME_PATHS_WINDOWS:
            if os.path.isfile(path):
                return path
        return None
    else:
        for candidate in ("google-chrome", "chromium-browser", "chromium",
                          "google-chrome-stable"):
            try:
                result = subprocess.run(["which", candidate],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except Exception:
                continue
        return None


# ---------------------------------------------------------------------------
# First-Run Setup Dialog
# ---------------------------------------------------------------------------

class SetupDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, config: dict):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.result = None

        self.title("Gertrude Shell - First-Time Setup")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        self.grab_set()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.update_idletasks()
        x = (self.winfo_screenwidth()  - self.winfo_width())  // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        pad = {"padx": 16, "pady": 8}

        tk.Label(self, text="Welcome to Gertrude Shell",
                 font=("Segoe UI", 18, "bold"),
                 bg=BG_MAIN, fg=FG_TITLE).pack(**pad, pady=(16, 4))

        tk.Label(self,
                 text="Choose which apps to show on the main board.\n"
                      "You can change this later by deleting config.json.",
                 font=FONT_SETUP, bg=BG_MAIN, fg=FG_GREETING,
                 justify=tk.LEFT).pack(**pad, pady=(0, 8))

        apps_frame = tk.LabelFrame(self, text="  Apps to enable  ",
                                   font=FONT_SETUP, bg=BG_MAIN, fg=FG_TITLE,
                                   padx=12, pady=8)
        apps_frame.pack(padx=16, pady=4, fill=tk.X)

        self._app_vars: dict[str, tk.BooleanVar] = {}
        apps_cfg = self.config.get("apps", {})
        for app in ALL_APPS:
            key = app["key"]
            var = tk.BooleanVar(value=apps_cfg.get(key, {}).get("enabled", True))
            self._app_vars[key] = var
            tk.Checkbutton(apps_frame,
                           text=app["label"].replace("\n", " "),
                           variable=var, font=FONT_SETUP,
                           bg=BG_MAIN, fg=FG_TITLE,
                           activebackground=BG_MAIN,
                           selectcolor=BG_MAIN).pack(anchor=tk.W, pady=2)

        cred_frame = tk.LabelFrame(self, text="  Login Credentials (optional)  ",
                                   font=FONT_SETUP, bg=BG_MAIN, fg=FG_TITLE,
                                   padx=12, pady=8)
        cred_frame.pack(padx=16, pady=4, fill=tk.X)

        tk.Label(cred_frame,
                 text="Note: stored with basic encoding only, NOT encrypted.\n"
                      "Once signed in, Chrome remembers Gertrude automatically.",
                 font=("Segoe UI", 10, "italic"),
                 bg=BG_MAIN, fg="#888888",
                 wraplength=380, justify=tk.LEFT).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))

        creds = self.config.get("credentials", {})
        self._cred_vars: dict[str, tk.StringVar] = {}
        fields = [
            ("facebook_user", "Facebook Username:"),
            ("facebook_pass", "Facebook Password:"),
            ("aol_user",      "AOL Username:"),
            ("aol_pass",      "AOL Password:"),
        ]
        for row, (key, label) in enumerate(fields, start=1):
            existing = shell_logic.decode_credential(creds.get(key, ""))
            var = tk.StringVar(value=existing)
            self._cred_vars[key] = var
            tk.Label(cred_frame, text=label, font=FONT_SETUP,
                     bg=BG_MAIN, fg=FG_TITLE).grid(
                row=row, column=0, sticky=tk.W, pady=3)
            tk.Entry(cred_frame, textvariable=var, font=FONT_SETUP,
                     show="*" if "pass" in key else "",
                     width=28).grid(
                row=row, column=1, sticky=tk.W, padx=(8, 0), pady=3)

        tk.Button(self, text="Save and Start",
                  font=("Segoe UI", 14, "bold"),
                  bg="#4CAF50", fg="#FFFFFF",
                  activebackground="#45A049", activeforeground="#FFFFFF",
                  relief=tk.RAISED, bd=3, padx=20, pady=8,
                  command=self._on_save).pack(pady=(8, 16))

    def _on_save(self):
        for key, var in self._app_vars.items():
            self.config["apps"].setdefault(key, {})["enabled"] = var.get()
        self.config.setdefault("credentials", {})
        for key, var in self._cred_vars.items():
            self.config["credentials"][key] = shell_logic.encode_credential(var.get())
        self.config["first_run"] = False
        self.result = self.config
        self.destroy()

    def _on_close(self):
        # Mark first_run done even if user just closed the dialog,
        # so it never appears automatically again.
        self.config["first_run"] = False
        shell_logic.save_config(self.config, CONFIG_PATH)
        self.result = self.config
        self.destroy()


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class GertrudeShell(tk.Tk):
    """
    Main board layout:
      Outer bevel (warm tan, always visible)
        Title bar: "Gertrude's Computer"  [END]
        Inner board (shows EITHER main content OR is empty while app is open)
          _board_content frame:
            Greeting label
            Photo
            App buttons
    """

    def __init__(self):
        super().__init__()

        # Make fully transparent while building — more reliable than withdraw()
        # on Windows because state("zoomed") can un-withdraw a withdrawn window.
        self.wm_attributes("-alpha", 0)

        self._config = shell_logic.load_config(CONFIG_PATH)
        self._chrome_procs: list[subprocess.Popen] = []
        self._active_url: Optional[str] = None
        self._banner_win: Optional[tk.Toplevel] = None

        self.title("Gertrude Shell")
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)

        os.makedirs(PROFILE_DIR, exist_ok=True)

        self._build_ui()
        self._refresh_greeting()

        # Show fully formed, maximised
        if platform.system() == "Windows":
            self.state("zoomed")
        else:
            self.geometry("1024x768")
        self.wm_attributes("-alpha", 1)

    # ------------------------------------------------------------------ #
    # UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        # Outer bevel
        self._outer_frame = tk.Frame(self, bg=BG_BEVEL_OUTER,
                                     relief=tk.RIDGE, bd=6,
                                     padx=6, pady=6)
        self._outer_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Inner board
        self._board = tk.Frame(self._outer_frame, bg=BG_BOARD,
                               relief=tk.SUNKEN, bd=4)
        self._board.pack(fill=tk.BOTH, expand=True)

        self._build_title_bar()

        # _board_content holds everything that hides when an app is open
        self._board_content = tk.Frame(self._board, bg=BG_BOARD)
        self._board_content.pack(fill=tk.BOTH, expand=True)

        self._build_greeting()
        self._build_photo_row()
        self._build_app_buttons()

    def _build_title_bar(self):
        bar = tk.Frame(self._board, bg=BG_BEVEL_OUTER, pady=6)
        bar.pack(fill=tk.X, side=tk.TOP)

        tk.Label(bar, text="Gertrude's Computer",
                 font=FONT_TITLE, bg=BG_BEVEL_OUTER,
                 fg="#FFFFFF", padx=16).pack(side=tk.LEFT)

        # Small ⚙ Settings button for caregiver access (left of END)
        tk.Button(bar, text="⚙", font=("Segoe UI", 12),
                  bg=BG_BEVEL_OUTER, fg="#FFFFFF",
                  activebackground="#A08050", activeforeground="#FFFFFF",
                  relief=tk.FLAT, bd=0, padx=6, pady=4,
                  cursor="hand2", command=self._show_setup
                  ).pack(side=tk.RIGHT, padx=(0, 4), pady=4)

        self._end_button = tk.Button(
            bar, text="END",
            font=("Segoe UI", 18, "bold"),
            bg="#CC0000", fg="#FFFFFF",
            activebackground="#FF3333", activeforeground="#FFFFFF",
            relief=tk.RAISED, bd=5,
            padx=22, pady=10,
            cursor="hand2", command=self._on_end_button)
        self._end_button.pack(side=tk.RIGHT, padx=16, pady=6)

    def _build_greeting(self):
        self._greeting_var = tk.StringVar()
        self._greeting_label = tk.Label(
            self._board_content,
            textvariable=self._greeting_var,
            font=("Segoe UI", 22, "bold"),
            bg=BG_BOARD, fg=FG_GREETING, pady=10)
        self._greeting_label.pack(fill=tk.X, padx=16)

    def _build_photo_row(self):
        row = tk.Frame(self._board_content, bg=BG_BOARD)
        row.pack(pady=(0, 16))
        self._make_photo_widget(row, "Gertrude & Marty",
                                "gertrude_and_marty.jpg",
                                width=260, height=320)

    def _make_photo_widget(self, parent, label_text, filename,
                           width=260, height=320):
        container = tk.Frame(parent, bg=BG_BOARD)
        container.pack(side=tk.LEFT)

        photo_loaded = False

        # Try exact name, then common extensions, then ANY image in the folder
        base, _ = os.path.splitext(filename)
        candidates = [filename]
        for ext in (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"):
            alt = base + ext
            if alt not in candidates:
                candidates.append(alt)

        if PILLOW_AVAILABLE:
            # Named candidates first
            for name in candidates:
                path = os.path.join(PHOTOS_DIR, name)
                if os.path.isfile(path):
                    try:
                        img = Image.open(path).resize((width, height), Image.LANCZOS)
                        tk_img = ImageTk.PhotoImage(img)
                        lbl = tk.Label(container, image=tk_img,
                                       bg=BG_BOARD, bd=4, relief=tk.GROOVE)
                        lbl.image = tk_img
                        lbl.pack()
                        photo_loaded = True
                        break
                    except Exception:
                        continue

            # Fallback: any image file in the photos folder
            if not photo_loaded and os.path.isdir(PHOTOS_DIR):
                try:
                    all_imgs = sorted([
                        f for f in os.listdir(PHOTOS_DIR)
                        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
                        and not f.startswith(".")
                    ])
                    for name in all_imgs:
                        path = os.path.join(PHOTOS_DIR, name)
                        try:
                            img = Image.open(path).resize((width, height), Image.LANCZOS)
                            tk_img = ImageTk.PhotoImage(img)
                            lbl = tk.Label(container, image=tk_img,
                                           bg=BG_BOARD, bd=4, relief=tk.GROOVE)
                            lbl.image = tk_img
                            lbl.pack()
                            photo_loaded = True
                            break
                        except Exception:
                            continue
                except Exception:
                    pass

        if not photo_loaded:
            canvas = tk.Canvas(container, width=width, height=height,
                               bg="#B8A090",
                               highlightthickness=4,
                               highlightbackground="#A09070")
            canvas.pack()
            canvas.create_text(width // 2, height // 2 - 20,
                               text="\U0001f491",
                               font=("Segoe UI Emoji", 48),
                               fill=FG_PHOTO_LABEL, anchor=tk.CENTER)
            canvas.create_text(width // 2, height // 2 + 30,
                               text=label_text,
                               font=FONT_PHOTO,
                               fill=FG_PHOTO_LABEL, anchor=tk.CENTER)

        tk.Label(container, text=label_text, font=FONT_PHOTO,
                 bg=BG_BOARD, fg=FG_GREETING).pack(pady=(6, 0))

    def _build_app_buttons(self):
        self._buttons_frame = tk.Frame(self._board_content, bg=BG_BOARD)
        self._buttons_frame.pack(pady=16, expand=True)
        self._redraw_app_buttons()

    def _redraw_app_buttons(self):
        for w in self._buttons_frame.winfo_children():
            w.destroy()

        active_apps = shell_logic.get_active_apps(ALL_APPS, self._config)
        if not active_apps:
            tk.Label(self._buttons_frame,
                     text="No apps enabled. Delete config.json to reset.",
                     font=FONT_SETUP, bg=BG_BOARD, fg=FG_GREETING).pack(pady=20)
            return

        COLS = 3
        for idx, app in enumerate(active_apps):
            row, col = idx // COLS, idx % COLS
            btn = tk.Button(
                self._buttons_frame,
                text=app["label"],
                font=FONT_BUTTON,
                bg=app["color"], fg=app["fg"],
                activebackground=self._lighten(app["color"]),
                activeforeground=app["fg"],
                relief=tk.RAISED, bd=4,
                padx=24, pady=16, width=14,
                wraplength=140, cursor="hand2",
                command=lambda a=app: self._on_app_button(a))
            btn.grid(row=row, column=col, padx=10, pady=10, sticky=tk.NSEW)

        for col in range(min(COLS, len(active_apps))):
            self._buttons_frame.grid_columnconfigure(col, weight=1)

    # ------------------------------------------------------------------ #
    # Greeting                                                             #
    # ------------------------------------------------------------------ #

    def _refresh_greeting(self):
        if self._active_url is None:
            self._greeting_var.set(shell_logic.get_greeting(datetime.now().hour))
        else:
            friendly = shell_logic.get_app_display_name(self._active_url)
            self._greeting_var.set(f"Now open: {friendly}")
        self.after(GREETING_REFRESH_MS, self._refresh_greeting)

    # ------------------------------------------------------------------ #
    # Button callbacks                                                     #
    # ------------------------------------------------------------------ #

    def _on_app_button(self, app: dict):
        url = app["url"]
        if not shell_logic.is_safe_url(url):
            messagebox.showerror("Blocked",
                f"This URL is not on the safe list and cannot be opened.\n{url}")
            return

        if url == "desktop":
            self._show_desktop()
            return

        self._active_url = url
        friendly = shell_logic.get_app_display_name(url)

        # Hide the main board, show the banner, then open Chrome positioned
        # to start exactly below the banner so no content is obscured.
        self.withdraw()
        self._open_banner(friendly)
        self._launch_chrome(url)

    def _open_banner(self, app_name: str):
        """Create a full-width always-on-top banner showing the app name + END button."""
        if self._banner_win is not None:
            try:
                self._banner_win.destroy()
            except Exception:
                pass

        # Standalone Toplevel (no parent) so it is never affected by the
        # parent window being withdrawn — this is the most reliable way to
        # keep the banner visible and correctly positioned on Windows.
        win = tk.Toplevel()
        win.overrideredirect(True)          # No OS title bar on the banner itself

        screen_w = win.winfo_screenwidth()
        win.geometry(f"{screen_w}x{BANNER_H}+0+0")
        win.attributes("-topmost", True)
        win.configure(bg=BG_BEVEL_OUTER)

        # Inner padding frame
        inner = tk.Frame(win, bg=BG_BEVEL_OUTER)
        inner.pack(fill=tk.BOTH, expand=True, padx=14, pady=16)

        # Title on the left
        tk.Label(inner, text="Gertrude's Computer",
                 font=("Segoe UI", 26, "bold"),
                 bg=BG_BEVEL_OUTER, fg="#FFFFFF",
                 padx=12).pack(side=tk.LEFT)

        # App name in the centre
        tk.Label(inner, text=f"Now open: {app_name}",
                 font=("Segoe UI", 20),
                 bg=BG_BEVEL_OUTER, fg="#FFF5CC").pack(side=tk.LEFT, padx=20)

        # Big red END button on the right
        tk.Button(inner, text="END",
                  font=("Segoe UI", 26, "bold"),
                  bg="#CC0000", fg="#FFFFFF",
                  activebackground="#FF3333", activeforeground="#FFFFFF",
                  relief=tk.RAISED, bd=5,
                  padx=36, pady=20,
                  cursor="hand2",
                  command=self._on_end_button
                  ).pack(side=tk.RIGHT, padx=16)

        win.update_idletasks()
        self._banner_win = win

    def _on_end_button(self):
        """Close all Chrome windows, destroy the banner, restore the full board."""
        self._close_all_chrome()
        self._active_url = None

        # Destroy the floating banner
        if self._banner_win is not None:
            try:
                self._banner_win.destroy()
            except Exception:
                pass
            self._banner_win = None

        # Restore main window
        self.deiconify()
        if platform.system() == "Windows":
            self.state("zoomed")

        self._greeting_var.set(shell_logic.get_greeting(datetime.now().hour))

    def _launch_chrome(self, url: str):
        chrome_path = find_chrome()
        if not chrome_path:
            messagebox.showwarning(
                "Chrome Not Found",
                "Google Chrome could not be found on this computer.\n\n"
                "Please install Chrome, or ask a family member for help.")
            return

        # Position Chrome to start exactly at the bottom edge of the banner
        # so the top of the page is never hidden behind it.
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        args = [
            chrome_path,
            f"--user-data-dir={PROFILE_DIR}",
            "--new-window",
            f"--window-position=0,{BANNER_H}",
            f"--window-size={screen_w},{screen_h - BANNER_H}",
            f"--app={url}",
        ]

        try:
            proc = subprocess.Popen(args,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            self._chrome_procs.append(proc)
        except OSError as exc:
            messagebox.showerror("Could Not Open",
                f"There was a problem opening this app.\n\nDetails: {exc}")

    def _show_desktop(self):
        if platform.system() == "Windows":
            try:
                subprocess.Popen(
                    ["cmd", "/c",
                     "explorer.exe shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    shell=False)
            except Exception:
                pass
        self.iconify()

    def _close_all_chrome(self):
        still_alive = []
        for proc in self._chrome_procs:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except OSError:
                pass
            if proc.poll() is None:
                still_alive.append(proc)
        self._chrome_procs = still_alive

    # ------------------------------------------------------------------ #
    # First-run setup                                                      #
    # ------------------------------------------------------------------ #

    def _show_setup(self):
        dialog = SetupDialog(self, self._config)
        self.wait_window(dialog)
        if dialog.result is not None:
            self._config = dialog.result
            try:
                shell_logic.save_config(self._config, CONFIG_PATH)
            except OSError as exc:
                messagebox.showwarning("Could Not Save Settings",
                    f"Your settings could not be saved.\n\nDetails: {exc}")
        self._redraw_app_buttons()

    # ------------------------------------------------------------------ #
    # Utilities                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _lighten(hex_color: str, amount: int = 40) -> str:
        try:
            h = hex_color.lstrip("#")
            r = min(255, int(h[0:2], 16) + amount)
            g = min(255, int(h[2:4], 16) + amount)
            b = min(255, int(h[4:6], 16) + amount)
            return f"#{r:02X}{g:02X}{b:02X}"
        except (ValueError, IndexError):
            return hex_color


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = GertrudeShell()

    def on_closing():
        app._close_all_chrome()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
