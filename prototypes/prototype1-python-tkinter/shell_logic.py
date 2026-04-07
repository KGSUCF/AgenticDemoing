"""
Gertrude Shell - Business Logic (shell_logic.py)
=================================================
Pure functions with no GUI dependencies. All state-free and testable.
This module is the "brain" of the Gertrude Shell; the tkinter GUI in
gertrude_shell.py calls these functions to keep display logic separate
from business logic.

Usage:
    import shell_logic
    greeting = shell_logic.get_greeting(datetime.now().hour)
"""

import json
import os
import base64
from urllib.parse import urlparse
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Mapping from URL to friendly display name.
# Extend this dict to add new apps without touching GUI code.
_MILO_URL = (
    "https://photos.google.com/share/"
    "AF1QipNJPdaXpqnpWA4lwzgMgta8gjcUI3OORBzlSv9Ny9QHVte3s4c16CSE8GHf0pNssw"
    "?key=TTBGSzR5QU0xblJXR3hQY05JNnBMNDNxUmhHWGxn"
)

URL_DISPLAY_NAMES: dict[str, str] = {
    "https://www.facebook.com":  "Facebook",
    "https://photos.google.com": "Milo (Google Photos)",
    _MILO_URL:                   "Milo (Google Photos)",
    "https://www.aol.com":       "AOL News",
    "https://mail.aol.com":      "AOL Mail",
    "desktop":                   "Desktop",
}

# Whitelisted domains that are considered safe to open.
# Only exact hostname matches (or "desktop" special value) are allowed.
# This is a security measure to prevent arbitrary URL injection.
SAFE_DOMAINS: set[str] = {
    "www.facebook.com",
    "photos.google.com",
    "www.aol.com",
    "mail.aol.com",
}

# Default config returned when the config file is missing or corrupt.
DEFAULT_CONFIG: dict[str, Any] = {
    "first_run": True,
    "apps": {
        "facebook": {"enabled": True,  "label": "Facebook"},
        "milo":     {"enabled": True,  "label": "Milo (Google Photos)"},
        "aol_news": {"enabled": True,  "label": "AOL News"},
        "aol_mail": {"enabled": True,  "label": "AOL Mail"},
        "desktop":  {"enabled": True,  "label": "Desktop"},
    },
    # NOTE: base64 is obfuscation only, NOT encryption.
    # Do not store genuinely secret credentials here in production.
    "credentials": {
        "facebook_user": base64.b64encode(b"").decode("ascii"),
        "facebook_pass": base64.b64encode(b"").decode("ascii"),
        "aol_user":      base64.b64encode(b"").decode("ascii"),
        "aol_pass":      base64.b64encode(b"").decode("ascii"),
    },
}


# ---------------------------------------------------------------------------
# Greeting
# ---------------------------------------------------------------------------

def get_greeting(hour: int) -> str:
    """
    Return a personalised time-of-day greeting for Gertrude.

    Args:
        hour: The current hour in 24-hour format (0–23).

    Returns:
        A greeting string such as "Good Morning, Gertrude!"

    Time bands:
        0–11  → Morning
        12–17 → Afternoon
        18–23 → Evening
    """
    if hour < 12:
        period = "Morning"
    elif hour < 18:
        period = "Afternoon"
    else:
        period = "Evening"

    return f"Good {period}, Gertrude!"


# ---------------------------------------------------------------------------
# URL safety
# ---------------------------------------------------------------------------

def is_safe_url(url: str) -> bool:
    """
    Check whether *url* is on the pre-approved whitelist.

    Only URLs whose exact hostname appears in SAFE_DOMAINS are allowed.
    The special value "desktop" is also permitted (triggers show-desktop
    behaviour rather than opening a browser).

    Args:
        url: The URL string to validate.

    Returns:
        True if the URL is safe to open, False otherwise.

    Security note:
        Substring / prefix matching is intentionally avoided to prevent
        spoofing attacks such as "notfacebook.com" or "facebook.com.evil.com".
        Only exact hostname matching is used.
    """
    if not url:
        return False

    # Special non-URL action
    if url == "desktop":
        return True

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        return hostname in SAFE_DOMAINS
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Display name lookup
# ---------------------------------------------------------------------------

def get_app_display_name(url: str) -> str:
    """
    Return the friendly display name for a given app URL.

    Args:
        url: The app URL (or "desktop" special value).

    Returns:
        A human-readable name such as "Facebook" or "AOL Mail".
        Falls back to the raw URL string if no mapping exists.
    """
    return URL_DISPLAY_NAMES.get(url, url)


# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict[str, Any]:
    """
    Load the JSON config file from *path*.

    If the file doesn't exist or contains invalid JSON, a copy of
    DEFAULT_CONFIG is returned so the application can continue safely.

    Args:
        path: Absolute or relative path to config.json.

    Returns:
        A dict containing the application configuration.
    """
    if not os.path.exists(path):
        return _default_config()

    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return _default_config()


def save_config(config: dict[str, Any], path: str) -> None:
    """
    Persist *config* as formatted JSON to *path*.

    Args:
        config: The configuration dictionary to save.
        path:   Absolute or relative path where config.json will be written.

    Raises:
        OSError: If the file cannot be written (permissions, disk full, etc.).
    """
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=4)


def _default_config() -> dict[str, Any]:
    """Return a fresh deep-copy of DEFAULT_CONFIG."""
    import copy
    return copy.deepcopy(DEFAULT_CONFIG)


# ---------------------------------------------------------------------------
# Active app filtering
# ---------------------------------------------------------------------------

def get_active_apps(
    all_apps: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Filter *all_apps* to only those marked enabled in *config*.

    An app is included only when ``config["apps"][app["key"]]["enabled"]``
    is exactly ``True``. Apps with no entry in config are excluded.

    Args:
        all_apps: Full list of app definition dicts, each containing at
                  minimum a ``"key"`` field.
        config:   Configuration dict as returned by :func:`load_config`.

    Returns:
        A (potentially empty) list of app dicts whose 'enabled' flag is True.

    Example::

        active = get_active_apps(ALL_APPS, load_config("config.json"))
    """
    apps_config = config.get("apps", {})
    return [
        app
        for app in all_apps
        if apps_config.get(app["key"], {}).get("enabled", False) is True
    ]


# ---------------------------------------------------------------------------
# Credential helpers (base64 obfuscation — NOT encryption)
# ---------------------------------------------------------------------------

def encode_credential(plain_text: str) -> str:
    """
    Base64-encode a credential string for storage in config.json.

    NOTE: This is obfuscation only, NOT encryption. Anyone with file
    access can trivially decode these values. It merely prevents the
    password from being visible at a glance in a text editor.

    Args:
        plain_text: The raw credential string.

    Returns:
        A base64-encoded ASCII string safe for JSON storage.
    """
    return base64.b64encode(plain_text.encode("utf-8")).decode("ascii")


def decode_credential(encoded: str) -> str:
    """
    Decode a base64-encoded credential string.

    NOTE: This is obfuscation only, NOT encryption.

    Args:
        encoded: A base64-encoded ASCII string from config.json.

    Returns:
        The original plain-text credential string.
    """
    try:
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    except Exception:
        return ""
