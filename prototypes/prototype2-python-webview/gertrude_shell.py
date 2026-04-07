"""
Gertrude Shell — Prototype 2: pywebview Embedded Browser
=========================================================
Prototype 2 of 3 — Windows accessibility shell for Gertrude (age 103).

Architecture
------------
* A single pywebview window whose WebView2 engine handles all browsing.
* ``storage_path`` points to a persistent user-data directory so Facebook
  and AOL Mail sessions survive between application restarts — Gertrude
  only ever has to sign in once.
* The main board is a local HTML file (main_board.html) that uses pywebview's
  js_api bridge to call Python functions.
* When an external app is open, a floating END-button header is injected into
  the live DOM on every page load, so Gertrude can always return home.

Run with
--------
    pip install pywebview Pillow
    python gertrude_shell.py

Compatibility
-------------
* Windows 10 / 11 (WebView2 required — ships with Win10 20H2+, or install
  from https://developer.microsoft.com/en-us/microsoft-edge/webview2/).
* macOS / Linux supported for development (uses WebKit via pywebview's
  gtk / cocoa backend).
"""

import base64
import os
import platform
import subprocess
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Path setup — allow import of shell_logic from the same directory
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import shell_logic  # noqa: E402  (local module, must come after sys.path fix)

import webview  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CONFIG_PATH    = os.path.join(_HERE, "config.json")
PHOTOS_DIR     = os.path.join(_HERE, "photos")
MAIN_BOARD_URL = "file:///" + os.path.join(_HERE, "main_board.html").replace("\\", "/")

# Persistent WebView2 user-data directory (cookies / localStorage survive restart).
# On Windows this lands in %APPDATA%\GertrudeShell\webview_data.
if platform.system() == "Windows":
    _APPDATA = os.environ.get("APPDATA", os.path.expanduser("~"))
    STORAGE_PATH = os.path.join(_APPDATA, "GertrudeShell", "webview_data")
else:
    STORAGE_PATH = os.path.join(os.path.expanduser("~"), ".gertrude_shell", "webview_data")

# ---------------------------------------------------------------------------
# JavaScript to inject a persistent END-button header into external pages
# ---------------------------------------------------------------------------
_INJECT_HEADER_JS = r"""
(function () {
    'use strict';
    var HEADER_ID = 'gertrude-persistent-header';
    if (document.getElementById(HEADER_ID)) { return; }

    var header = document.createElement('div');
    header.id = HEADER_ID;
    header.style.cssText = [
        'position:fixed',
        'top:0',
        'left:0',
        'right:0',
        'height:64px',
        'background:rgba(200,169,122,0.97)',
        'display:flex',
        'align-items:center',
        'justify-content:space-between',
        'padding:0 16px',
        'z-index:2147483647',
        'box-shadow:0 2px 8px rgba(0,0,0,0.45)',
        'box-sizing:border-box',
    ].join(';');

    /* App / page name label */
    var nameLabel = document.createElement('span');
    nameLabel.id  = 'gertrude-app-name';
    nameLabel.style.cssText = [
        'font-family:Segoe UI,Arial,sans-serif',
        'font-size:20px',
        'font-weight:bold',
        'color:#fff',
        'max-width:calc(100% - 90px)',
        'overflow:hidden',
        'white-space:nowrap',
        'text-overflow:ellipsis',
    ].join(';');

    /* Derive a friendly name from the current hostname */
    var host = window.location.hostname.replace(/^www\./, '');
    var nameMap = {
        'facebook.com':     'Facebook',
        'photos.google.com':'Milo (Photos)',
        'aol.com':          'AOL News',
        'mail.aol.com':     'AOL Mail',
    };
    nameLabel.textContent = nameMap[host] || document.title || host;

    /* END button */
    var endBtn = document.createElement('button');
    endBtn.textContent = 'END';
    endBtn.title       = 'Return to main board';
    endBtn.style.cssText = [
        'width:62px',
        'height:62px',
        'border-radius:50%',
        'background:#CC0000',
        'color:#fff',
        'border:3px solid #fff',
        'font-family:Segoe UI,Arial,sans-serif',
        'font-size:17px',
        'font-weight:bold',
        'cursor:pointer',
        'flex-shrink:0',
        'box-shadow:0 2px 6px rgba(0,0,0,0.5)',
    ].join(';');
    endBtn.onmouseover = function () { this.style.background = '#FF0000'; };
    endBtn.onmouseout  = function () { this.style.background = '#CC0000'; };
    endBtn.onclick     = function () {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.go_home();
        }
    };

    header.appendChild(nameLabel);
    header.appendChild(endBtn);
    document.body.insertBefore(header, document.body.firstChild);

    /* Push page content down so nothing hides behind the header */
    document.documentElement.style.paddingTop =
        (parseInt(document.documentElement.style.paddingTop || '0') + 64) + 'px';
}());
"""


# ---------------------------------------------------------------------------
# Python API (exposed to JavaScript via pywebview js_api)
# ---------------------------------------------------------------------------

class GertrudeAPI:
    """
    All public methods here are callable from JavaScript as::

        window.pywebview.api.method_name(args)

    pywebview serialises/deserialises arguments and return values as JSON.
    """

    def __init__(self) -> None:
        self._window = None          # Set after webview.create_window()
        self._config = shell_logic.load_config(CONFIG_PATH)
        self._current_app_id: str | None = None

    # ------------------------------------------------------------------
    # Greeting
    # ------------------------------------------------------------------

    def get_full_greeting(self) -> str:
        """Return the time-appropriate personalised greeting string."""
        hour = datetime.now().hour
        return shell_logic.get_full_greeting(hour, "Gertrude")

    # ------------------------------------------------------------------
    # App list
    # ------------------------------------------------------------------

    def get_apps(self) -> list[dict]:
        """Return the list of enabled apps for the main board."""
        enabled = self._config.get("apps_enabled", [app["id"] for app in shell_logic.APP_REGISTRY])
        return [
            {
                "id":         app["id"],
                "label":      app["label"],
                "bg_color":   app["bg_color"],
                "fg_color":   app["fg_color"],
            }
            for app in shell_logic.APP_REGISTRY
            if app["id"] in enabled
        ]

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate_to_app(self, app_id: str) -> dict:
        """
        Navigate the webview window to the given app.

        Returns a dict ``{"success": bool, "reason": str}``.
        """
        app = shell_logic.get_app_by_id(app_id)
        if not app:
            return {"success": False, "reason": "Unknown app ID."}

        if app_id == "desktop":
            self._show_desktop()
            return {"success": True, "reason": ""}

        url = app["url"]
        safety = shell_logic.check_navigation_safety(
            url, self._config.get("whitelist", shell_logic.DEFAULT_CONFIG["whitelist"])
        )
        if not safety["safe"]:
            return {"success": False, "reason": safety["reason"]}

        self._current_app_id = app_id
        if self._window:
            self._window.load_url(url)
        return {"success": True, "reason": "", "display_name": app["display_name"]}

    def go_home(self) -> None:
        """Navigate back to the main board HTML page."""
        self._current_app_id = None
        if self._window:
            self._window.load_url(MAIN_BOARD_URL)

    def check_url_safety(self, url: str) -> dict:
        """Check whether a URL is safe. Called from JavaScript before navigation."""
        return shell_logic.check_navigation_safety(
            url, self._config.get("whitelist", shell_logic.DEFAULT_CONFIG["whitelist"])
        )

    # ------------------------------------------------------------------
    # Photo
    # ------------------------------------------------------------------

    def get_photo_data(self) -> str | None:
        """
        Return the combined Gertrude-and-Marty photo as a base64-encoded
        string (JPEG), or None if the file is not yet present.

        The HTML page embeds it directly as a data-URI:
            <img src="data:image/jpeg;base64,{data}">
        """
        for name in ("gertrude_and_marty.jpg", "gertrude_and_marty.png",
                     "gertrude.jpg", "gertrude.png"):
            photo_path = os.path.join(PHOTOS_DIR, name)
            if os.path.isfile(photo_path):
                try:
                    with open(photo_path, "rb") as fh:
                        raw = fh.read()
                    ext = "png" if name.endswith(".png") else "jpeg"
                    return f"data:image/{ext};base64," + base64.b64encode(raw).decode("ascii")
                except Exception:
                    pass
        return None

    # ------------------------------------------------------------------
    # First-run setup
    # ------------------------------------------------------------------

    def get_setup_info(self) -> dict:
        """Return first-run flag and current app-enabled list."""
        return {
            "first_run":    self._config.get("first_run", True),
            "apps_enabled": self._config.get("apps_enabled",
                                             [a["id"] for a in shell_logic.APP_REGISTRY]),
            "all_apps": [
                {"id": a["id"], "label": a["label"].replace("\n", " ")}
                for a in shell_logic.APP_REGISTRY
            ],
        }

    def save_setup(self, apps_enabled: list[str],
                   fb_user: str, fb_pass: str,
                   aol_user: str, aol_pass: str) -> None:
        """
        Persist first-run setup choices.

        Credentials are base64-encoded (obfuscation only, NOT encryption).
        Login sessions themselves are persisted by WebView2's storage_path,
        so Gertrude will stay logged in between app restarts automatically.
        """
        self._config["apps_enabled"] = apps_enabled
        self._config["first_run"]    = False
        self._config["credentials"] = {
            "facebook_user": shell_logic.encode_credential(fb_user),
            "facebook_pass": shell_logic.encode_credential(fb_pass),
            "aol_user":      shell_logic.encode_credential(aol_user),
            "aol_pass":      shell_logic.encode_credential(aol_pass),
        }
        shell_logic.save_config(self._config, CONFIG_PATH)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _show_desktop(self) -> None:
        """Minimise the window to reveal the Windows desktop."""
        if platform.system() == "Windows":
            try:
                subprocess.Popen(
                    ["cmd", "/c",
                     "explorer.exe shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False,
                )
            except Exception:
                pass
        if self._window:
            self._window.minimize()


# ---------------------------------------------------------------------------
# pywebview event callbacks
# ---------------------------------------------------------------------------

def _on_loaded(window: webview.Window, api: GertrudeAPI) -> None:
    """
    Called after every page finishes loading.

    For the main board (file:// URL) we do nothing — its HTML already has the
    END button baked in.  For any external HTTPS page we inject the floating
    persistent header so Gertrude can always see the END button.
    """
    try:
        url: str = window.get_current_url() or ""
    except Exception:
        url = ""

    # Don't inject on the local main board — it has its own END button
    is_main_board = url.startswith("file://") or url == "" or url == "about:blank"
    if not is_main_board:
        window.evaluate_js(_INJECT_HEADER_JS)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Create the pywebview window and start the event loop."""
    os.makedirs(STORAGE_PATH, exist_ok=True)

    api = GertrudeAPI()

    window = webview.create_window(
        title="Gertrude's Computer",
        url=MAIN_BOARD_URL,
        js_api=api,
        fullscreen=True,
        easy_drag=False,
        background_color="#FFF8F0",
        text_select=False,
    )
    api._window = window

    # Wire up the loaded event (pywebview ≥ 4.0 event API)
    window.events.loaded += lambda: _on_loaded(window, api)

    webview.start(
        debug=False,
        # storage_path persists cookies / localStorage between runs (login persistence).
        storage_path=STORAGE_PATH,
    )


if __name__ == "__main__":
    main()
