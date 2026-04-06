"""
Gertrude Shell - Main tkinter Application (gertrude_shell.py)
=============================================================
Prototype 1 of 3 - Windows accessibility shell for Gertrude (age 103).

This module contains the full tkinter GUI. All business logic lives in
shell_logic.py so this file stays focused on presentation and user
interaction.

Run with:
    python gertrude_shell.py

Requirements:
    Python 3.8+, tkinter (built-in), Pillow (pip install Pillow)
    See requirements.txt for full dependency list.

Compatibility:
    Windows 7, 8, 10, 11 - tested with Python 3.8 through 3.12.
"""

import sys
import os
import subprocess
import platform
import tkinter as tk
from tkinter import messagebox, font as tkfont
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Optional Pillow import (used for loading real photos when available)
# ---------------------------------------------------------------------------
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# ---------------------------------------------------------------------------
# Local business-logic module
# ---------------------------------------------------------------------------
# Allow running from any working directory by adding the script's directory
# to sys.path first.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import shell_logic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = os.path.join(_HERE, "config.json")
PHOTOS_DIR  = os.path.join(_HERE, "photos")

# Chrome executable paths to try, in priority order.
# On Windows, Chrome is commonly installed in one of these locations.
CHROME_PATHS_WINDOWS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

# ---------------------------------------------------------------------------
# App definitions (static list; enable/disable state lives in config.json)
# ---------------------------------------------------------------------------

ALL_APPS = [
    {
        "key":   "facebook",
        "label": "Facebook",
        "url":   "https://www.facebook.com",
        "color": "#1877F2",   # Facebook blue
        "fg":    "#FFFFFF",
    },
    {
        "key":   "milo",
        "label": "Milo\n(Google Photos)",
        "url":   "https://photos.google.com",
        "color": "#34A853",   # Google green
        "fg":    "#FFFFFF",
    },
    {
        "key":   "aol_news",
        "label": "AOL News",
        "url":   "https://www.aol.com",
        "color": "#FF0000",   # AOL red
        "fg":    "#FFFFFF",
    },
    {
        "key":   "aol_mail",
        "label": "AOL Mail",
        "url":   "https://mail.aol.com",
        "color": "#FF6600",   # AOL orange
        "fg":    "#FFFFFF",
    },
    {
        "key":   "desktop",
        "label": "Desktop",
        "url":   "desktop",
        "color": "#5C5C8A",   # Muted purple
        "fg":    "#FFFFFF",
    },
]

# ---------------------------------------------------------------------------
# Colour and font constants for the warm, accessible theme
# ---------------------------------------------------------------------------

BG_MAIN         = "#FFF8F0"   # Warm off-white background
BG_BOARD        = "#FFF3E0"   # Slightly warmer board interior
BG_BEVEL_OUTER  = "#C8A97A"   # Warm tan for outer bevel
BG_BEVEL_INNER  = "#E8D5B7"   # Lighter inner bevel

FG_TITLE        = "#4A2C0A"   # Dark warm brown for title text
FG_GREETING     = "#6B3A10"   # Medium brown for greeting
FG_PHOTO_LABEL  = "#FFFFFF"   # White on photo placeholder canvas

FONT_TITLE    = ("Segoe UI", 24, "bold")
FONT_GREETING = ("Segoe UI", 20)
FONT_BUTTON   = ("Segoe UI", 16, "bold")
FONT_PHOTO    = ("Segoe UI", 14, "bold")
FONT_END      = ("Segoe UI", 14, "bold")
FONT_SETUP    = ("Segoe UI", 13)

GREETING_REFRESH_MS = 60_000   # Re-check time every 60 seconds

# ---------------------------------------------------------------------------
# Helper: find Chrome executable
# ---------------------------------------------------------------------------

def find_chrome() -> Optional[str]:
    """
    Return the path to the Chrome executable on the current platform.

    Tries a list of common installation locations on Windows.
    On other platforms (dev/test on macOS/Linux) tries 'google-chrome'
    and 'chromium-browser' on PATH.

    Returns:
        Path string if Chrome is found, None otherwise.
    """
    if platform.system() == "Windows":
        for path in CHROME_PATHS_WINDOWS:
            if os.path.isfile(path):
                return path
        return None
    else:
        # Non-Windows (development/testing) - try common names on PATH
        for candidate in ("google-chrome", "chromium-browser", "chromium",
                          "google-chrome-stable"):
            try:
                result = subprocess.run(
                    ["which", candidate],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except Exception:
                continue
        return None


# ---------------------------------------------------------------------------
# First-Run Setup Dialog
# ---------------------------------------------------------------------------

class SetupDialog(tk.Toplevel):
    """
    Modal dialog shown on first run to let the caregiver choose which
    apps to enable and optionally enter login credentials.

    The dialog saves results back to config.json and clears first_run flag.
    """

    def __init__(self, parent: tk.Tk, config: dict):
        super().__init__(parent)
        self.parent  = parent
        self.config  = config
        self.result  = None   # Will be set to updated config dict on Save

        self.title("Gertrude Shell - First-Time Setup")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        self.grab_set()  # Make modal

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - self.winfo_width())  // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Construct the setup dialog widgets."""
        pad = {"padx": 16, "pady": 8}

        # ---- Heading
        tk.Label(
            self, text="Welcome to Gertrude Shell",
            font=("Segoe UI", 18, "bold"),
            bg=BG_MAIN, fg=FG_TITLE
        ).pack(**pad, pady=(16, 4))

        tk.Label(
            self,
            text=(
                "Please choose which apps to show on the main board.\n"
                "You can change this later by deleting config.json."
            ),
            font=FONT_SETUP, bg=BG_MAIN, fg=FG_GREETING,
            justify=tk.LEFT
        ).pack(**pad, pady=(0, 8))

        # ---- App checkboxes
        apps_frame = tk.LabelFrame(
            self, text="  Apps to enable  ",
            font=FONT_SETUP, bg=BG_MAIN, fg=FG_TITLE,
            padx=12, pady=8
        )
        apps_frame.pack(padx=16, pady=4, fill=tk.X)

        self._app_vars: dict[str, tk.BooleanVar] = {}
        apps_cfg = self.config.get("apps", {})

        for app in ALL_APPS:
            key     = app["key"]
            enabled = apps_cfg.get(key, {}).get("enabled", True)
            var     = tk.BooleanVar(value=enabled)
            self._app_vars[key] = var
            tk.Checkbutton(
                apps_frame,
                text=app["label"].replace("\n", " "),
                variable=var,
                font=FONT_SETUP,
                bg=BG_MAIN, fg=FG_TITLE,
                activebackground=BG_MAIN,
                selectcolor=BG_MAIN
            ).pack(anchor=tk.W, pady=2)

        # ---- Credentials section
        cred_frame = tk.LabelFrame(
            self, text="  Login Credentials (optional)  ",
            font=FONT_SETUP, bg=BG_MAIN, fg=FG_TITLE,
            padx=12, pady=8
        )
        cred_frame.pack(padx=16, pady=4, fill=tk.X)

        tk.Label(
            cred_frame,
            text="Note: Credentials are stored with base64 obfuscation only - NOT encrypted.",
            font=("Segoe UI", 10, "italic"),
            bg=BG_MAIN, fg="#888888",
            wraplength=380, justify=tk.LEFT
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))

        creds = self.config.get("credentials", {})
        self._cred_vars: dict[str, tk.StringVar] = {}

        fields = [
            ("facebook_user", "Facebook Username:"),
            ("facebook_pass", "Facebook Password:"),
            ("aol_user",      "AOL Username:"),
            ("aol_pass",      "AOL Password:"),
        ]

        for row, (key, label) in enumerate(fields, start=1):
            # Decode existing value for display
            existing = shell_logic.decode_credential(creds.get(key, ""))
            var = tk.StringVar(value=existing)
            self._cred_vars[key] = var

            tk.Label(cred_frame, text=label, font=FONT_SETUP,
                     bg=BG_MAIN, fg=FG_TITLE).grid(
                row=row, column=0, sticky=tk.W, pady=3)
            show_char = "*" if "pass" in key else ""
            tk.Entry(cred_frame, textvariable=var,
                     font=FONT_SETUP, show=show_char, width=28).grid(
                row=row, column=1, sticky=tk.W, padx=(8, 0), pady=3)

        # ---- Save button
        tk.Button(
            self,
            text="Save and Start",
            font=("Segoe UI", 14, "bold"),
            bg="#4CAF50", fg="#FFFFFF",
            activebackground="#45A049", activeforeground="#FFFFFF",
            relief=tk.RAISED, bd=3,
            padx=20, pady=8,
            command=self._on_save
        ).pack(pady=(8, 16))

    def _on_save(self):
        """Collect values, update config dict, and close dialog."""
        # Update app enabled states
        for key, var in self._app_vars.items():
            if key not in self.config["apps"]:
                self.config["apps"][key] = {}
            self.config["apps"][key]["enabled"] = var.get()

        # Update credentials (base64-encoded)
        if "credentials" not in self.config:
            self.config["credentials"] = {}
        for key, var in self._cred_vars.items():
            self.config["credentials"][key] = shell_logic.encode_credential(var.get())

        # Clear first_run flag
        self.config["first_run"] = False

        self.result = self.config
        self.destroy()

    def _on_close(self):
        """If user closes dialog without saving, still dismiss the window."""
        self.config["first_run"] = False
        self.result = self.config
        self.destroy()


# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------

class GertrudeShell(tk.Tk):
    """
    Main application window for the Gertrude Shell accessibility interface.

    Layout:
        - Outer bevel frame (3D raised relief, warm tan)
        - Inner board (warm cream background)
          - Title bar at the top with END button (red circle) in upper-right
          - Greeting label (time-based, or active app name)
          - Photo row: Gertrude | spacer | Marty
          - App button grid
    """

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------
        # Load config and handle first-run setup
        # ------------------------------------------------------------------
        self._config = shell_logic.load_config(CONFIG_PATH)

        # List of subprocess.Popen objects for launched Chrome windows
        self._chrome_procs: list[subprocess.Popen] = []

        # Which app is currently open (URL string or None)
        self._active_url: Optional[str] = None

        # ------------------------------------------------------------------
        # Window basics
        # ------------------------------------------------------------------
        self.title("Gertrude Shell")
        self.configure(bg=BG_MAIN)

        # Start maximised on Windows; a sensible large size elsewhere
        if platform.system() == "Windows":
            self.state("zoomed")
        else:
            self.geometry("1024x768")

        self.resizable(True, True)

        # ------------------------------------------------------------------
        # Build the UI
        # ------------------------------------------------------------------
        self._build_ui()

        # ------------------------------------------------------------------
        # First-run: show setup dialog before main window appears
        # ------------------------------------------------------------------
        if self._config.get("first_run", True):
            self.after(100, self._show_setup)

        # ------------------------------------------------------------------
        # Start greeting refresh loop
        # ------------------------------------------------------------------
        self._refresh_greeting()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Build all top-level UI regions."""
        # Outer bevel frame - gives the 3D board effect
        self._outer_frame = tk.Frame(
            self,
            bg=BG_BEVEL_OUTER,
            relief=tk.RIDGE,
            bd=6,
            padx=6, pady=6
        )
        self._outer_frame.pack(
            fill=tk.BOTH, expand=True,
            padx=20, pady=20
        )

        # Inner board frame
        self._board = tk.Frame(
            self._outer_frame,
            bg=BG_BOARD,
            relief=tk.SUNKEN,
            bd=4
        )
        self._board.pack(fill=tk.BOTH, expand=True)

        # Build regions inside the board
        self._build_title_bar()
        self._build_greeting()
        self._build_photo_row()
        self._build_app_buttons()

    def _build_title_bar(self):
        """
        Title bar: application title on the left, END button on the right.
        The END button is styled as a prominent red circular button.
        """
        bar = tk.Frame(self._board, bg=BG_BEVEL_OUTER, pady=6)
        bar.pack(fill=tk.X, side=tk.TOP)

        # Title
        tk.Label(
            bar,
            text="Gertrude's Computer",
            font=FONT_TITLE,
            bg=BG_BEVEL_OUTER,
            fg="#FFFFFF",
            padx=16
        ).pack(side=tk.LEFT)

        # END button - visually prominent, red, circle-like (rounded with padx/pady)
        self._end_button = tk.Button(
            bar,
            text="END",
            font=FONT_END,
            bg="#CC0000",
            fg="#FFFFFF",
            activebackground="#FF0000",
            activeforeground="#FFFFFF",
            relief=tk.RAISED,
            bd=4,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_end_button
        )
        self._end_button.pack(side=tk.RIGHT, padx=12, pady=4)

        # Give the END button a rounded appearance using a round Canvas trick
        # (tkinter doesn't support native rounded buttons, so we use a slightly
        #  large font and generous padding to approximate a circle/oval)
        self._end_button.configure(font=("Segoe UI", 13, "bold"))

    def _build_greeting(self):
        """
        Greeting label below the title bar.
        Shows time-based greeting normally; shows active app name when open.
        """
        self._greeting_var = tk.StringVar()
        self._greeting_label = tk.Label(
            self._board,
            textvariable=self._greeting_var,
            font=("Segoe UI", 22, "bold"),
            bg=BG_BOARD,
            fg=FG_GREETING,
            pady=10
        )
        self._greeting_label.pack(fill=tk.X, padx=16)

    def _build_photo_row(self):
        """
        Photo row with two 150×150 placeholder canvases labelled
        'Gertrude' and 'Marty'.  If real photos exist in the photos/
        directory (gertrude.jpg / marty.jpg) and Pillow is available,
        the real images are shown instead.
        """
        row = tk.Frame(self._board, bg=BG_BOARD)
        row.pack(pady=(0, 16))

        self._make_photo_widget(row, "Gertrude", "gertrude.jpg")

        # Spacer
        tk.Frame(row, bg=BG_BOARD, width=60).pack(side=tk.LEFT)

        self._make_photo_widget(row, "Marty", "marty.jpg")

    def _make_photo_widget(self, parent: tk.Frame,
                           label_text: str,
                           filename: str):
        """
        Create a photo display widget (Canvas placeholder or real image).

        Args:
            parent:     The parent frame to pack into.
            label_text: Caption to display below / on the placeholder.
            filename:   Photo filename to look for in the photos/ directory.
        """
        container = tk.Frame(parent, bg=BG_BOARD)
        container.pack(side=tk.LEFT)

        photo_loaded = False
        photo_path   = os.path.join(PHOTOS_DIR, filename)

        if PILLOW_AVAILABLE and os.path.isfile(photo_path):
            try:
                img = Image.open(photo_path).resize((150, 150), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                lbl = tk.Label(container, image=tk_img,
                               bg=BG_BOARD, bd=3, relief=tk.GROOVE)
                lbl.image = tk_img   # Keep reference to prevent GC
                lbl.pack()
                photo_loaded = True
            except Exception:
                photo_loaded = False

        if not photo_loaded:
            # Gray placeholder canvas
            canvas = tk.Canvas(
                container,
                width=150, height=150,
                bg="#B0B0B0",
                highlightthickness=3,
                highlightbackground="#888888"
            )
            canvas.pack()
            # Centered text label on the placeholder
            canvas.create_rectangle(0, 0, 150, 150, fill="#B0B0B0", outline="")
            canvas.create_text(
                75, 75,
                text=label_text,
                font=FONT_PHOTO,
                fill=FG_PHOTO_LABEL,
                anchor=tk.CENTER
            )

        # Caption label below photo
        tk.Label(
            container,
            text=label_text,
            font=FONT_PHOTO,
            bg=BG_BOARD,
            fg=FG_GREETING
        ).pack(pady=(4, 0))

    def _build_app_buttons(self):
        """
        Build the grid of app buttons from the active (enabled) apps list.
        Buttons are large, high-contrast, and labelled with friendly names.
        """
        self._buttons_frame = tk.Frame(self._board, bg=BG_BOARD)
        self._buttons_frame.pack(pady=16, expand=True)

        # Store reference so we can rebuild after setup dialog
        self._redraw_app_buttons()

    def _redraw_app_buttons(self):
        """Clear and repopulate the app buttons grid from current config."""
        # Destroy any existing button widgets
        for widget in self._buttons_frame.winfo_children():
            widget.destroy()

        active_apps = shell_logic.get_active_apps(ALL_APPS, self._config)

        if not active_apps:
            tk.Label(
                self._buttons_frame,
                text="No apps enabled. Delete config.json to reset.",
                font=FONT_SETUP,
                bg=BG_BOARD, fg=FG_GREETING
            ).pack(pady=20)
            return

        # Lay out buttons in rows of up to 3
        COLS = 3
        for idx, app in enumerate(active_apps):
            row = idx // COLS
            col = idx % COLS

            btn = tk.Button(
                self._buttons_frame,
                text=app["label"],
                font=FONT_BUTTON,
                bg=app["color"],
                fg=app["fg"],
                activebackground=self._lighten(app["color"]),
                activeforeground=app["fg"],
                relief=tk.RAISED,
                bd=4,
                padx=24,
                pady=16,
                width=14,
                wraplength=140,
                cursor="hand2",
                command=lambda a=app: self._on_app_button(a)
            )
            btn.grid(row=row, column=col, padx=10, pady=10, sticky=tk.NSEW)

        # Make all columns equal width
        for col in range(min(COLS, len(active_apps))):
            self._buttons_frame.grid_columnconfigure(col, weight=1)

    # ------------------------------------------------------------------
    # Greeting refresh
    # ------------------------------------------------------------------

    def _refresh_greeting(self):
        """
        Update the greeting label based on the current time (or active app).
        Schedules itself to run again every GREETING_REFRESH_MS milliseconds.
        """
        if self._active_url is None:
            # Show time-based greeting
            hour = datetime.now().hour
            self._greeting_var.set(shell_logic.get_greeting(hour))
        else:
            # Show which app is currently open
            friendly = shell_logic.get_app_display_name(self._active_url)
            self._greeting_var.set(f"Now open: {friendly}")

        self.after(GREETING_REFRESH_MS, self._refresh_greeting)

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------

    def _on_app_button(self, app: dict):
        """
        Handle an app button click.

        Validates the URL against the safety whitelist, then either:
        - Launches Chrome with --app={url} for web apps, or
        - Triggers the show-desktop action for the 'desktop' key.

        Args:
            app: The app definition dict (key, label, url, color, fg).
        """
        url = app["url"]

        # Safety check - belt-and-suspenders even if UI only shows known apps
        if not shell_logic.is_safe_url(url):
            messagebox.showerror(
                "Blocked",
                f"This URL is not on the safe list and cannot be opened.\n{url}"
            )
            return

        if url == "desktop":
            self._show_desktop()
        else:
            self._launch_chrome(url)

        # Update greeting to show active app name
        self._active_url = url
        friendly = shell_logic.get_app_display_name(url)
        self._greeting_var.set(f"Now open: {friendly}")

    def _launch_chrome(self, url: str):
        """
        Launch a new Chrome window for the given URL.

        Uses --app flag to open Chrome in app mode (no browser chrome/tabs)
        which gives a cleaner, simpler look for Gertrude.

        All launched Popen objects are stored in self._chrome_procs so the
        END button can terminate them all.

        Args:
            url: The web URL to open.
        """
        chrome_path = find_chrome()

        if not chrome_path:
            messagebox.showwarning(
                "Chrome Not Found",
                "Google Chrome could not be found on this computer.\n\n"
                "Please install Chrome, or ask a family member for help."
            )
            return

        try:
            proc = subprocess.Popen(
                [chrome_path, "--new-window", f"--app={url}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._chrome_procs.append(proc)
        except OSError as exc:
            messagebox.showerror(
                "Could Not Open",
                f"There was a problem opening this app.\n\nDetails: {exc}"
            )

    def _show_desktop(self):
        """
        Minimise the Gertrude Shell window to reveal the desktop.

        On Windows this also triggers the 'show desktop' shortcut so all
        other windows are minimised too. On other platforms we just iconify.
        """
        if platform.system() == "Windows":
            try:
                # Win+D equivalent via the shell
                subprocess.Popen(
                    ["cmd", "/c", "explorer.exe shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False
                )
            except Exception:
                pass
        # Minimise Gertrude Shell itself regardless
        self.iconify()

    def _on_end_button(self):
        """
        END button callback.

        Terminates all Chrome windows launched by Gertrude Shell, then
        returns the display to the main board (clears the active app state
        and restores the time-based greeting).
        """
        self._close_all_chrome()
        self._active_url = None

        # If minimised (show-desktop), bring window back
        self.deiconify()
        self.lift()

        # Immediately refresh greeting to show time-based text again
        hour = datetime.now().hour
        self._greeting_var.set(shell_logic.get_greeting(hour))

    def _close_all_chrome(self):
        """
        Terminate every Chrome subprocess that was launched by this session.

        Uses proc.terminate() first (SIGTERM / graceful), then checks if the
        process is still alive and uses proc.kill() as a last resort.

        The internal list is cleared after attempting to close all processes.
        """
        still_alive = []
        for proc in self._chrome_procs:
            try:
                if proc.poll() is None:   # Still running
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except OSError:
                pass   # Process may already be gone

            # Only keep procs that are somehow still alive after kill
            if proc.poll() is None:
                still_alive.append(proc)

        self._chrome_procs = still_alive

    # ------------------------------------------------------------------
    # First-run setup
    # ------------------------------------------------------------------

    def _show_setup(self):
        """Show the first-run setup dialog and save the resulting config."""
        dialog = SetupDialog(self, self._config)
        self.wait_window(dialog)

        if dialog.result is not None:
            self._config = dialog.result
            try:
                shell_logic.save_config(self._config, CONFIG_PATH)
            except OSError as exc:
                messagebox.showwarning(
                    "Could Not Save Settings",
                    f"Your settings could not be saved.\n\nDetails: {exc}"
                )

        # Rebuild app buttons to reflect any changes from setup
        self._redraw_app_buttons()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _lighten(hex_color: str, amount: int = 40) -> str:
        """
        Return a slightly lighter version of a hex colour string.

        Used for button active/hover states.

        Args:
            hex_color: A 7-character hex colour string like "#1877F2".
            amount:    How much to lighten each channel (0-255).

        Returns:
            A lightened hex colour string.
        """
        try:
            hex_color = hex_color.lstrip("#")
            r = min(255, int(hex_color[0:2], 16) + amount)
            g = min(255, int(hex_color[2:4], 16) + amount)
            b = min(255, int(hex_color[4:6], 16) + amount)
            return f"#{r:02X}{g:02X}{b:02X}"
        except (ValueError, IndexError):
            return hex_color


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Launch the Gertrude Shell application."""
    app = GertrudeShell()

    # Handle window close (X button) gracefully: close Chrome, then exit
    def on_closing():
        app._close_all_chrome()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
