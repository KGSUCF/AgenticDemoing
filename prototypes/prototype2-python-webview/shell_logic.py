"""
shell_logic.py - Pure business logic for Gertrude Shell
No UI imports here; this module is fully unit-testable.

All functions are stateless and side-effect-free except load_config / save_config.
"""

import base64
import json
import os
from typing import Any
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "first_run": True,
    "user_name": "Gertrude",
    "whitelist": [
        "facebook.com",
        "photos.google.com",
        "google.com",
        "aol.com",
        "mail.aol.com",
    ],
    "apps_enabled": ["facebook", "milo", "aol_news", "aol_mail", "desktop"],
    "credentials": {},
}

# ---------------------------------------------------------------------------
# App registry: canonical app definitions
# ---------------------------------------------------------------------------

APP_REGISTRY = [
    {
        "id": "facebook",
        "label": "Facebook",
        "display_name": "Facebook",
        "url": "https://www.facebook.com",
        "domain_key": "facebook.com",
        "emoji": "\U0001f4f0",
        "bg_color": "#1877F2",
        "fg_color": "#FFFFFF",
    },
    {
        "id": "milo",
        "label": "Milo\n(Photos)",
        "display_name": "Milo (Photos)",
        # Gertrude's grandchild Milo — specific shared album
        "url": "https://photos.google.com/share/AF1QipNJPdaXpqnpWA4lwzgMgta8gjcUI3OORBzlSv9Ny9QHVte3s4c16CSE8GHf0pNssw?key=TTBGSzR5QU0xblJXR3hQY05JNnBMNDNxUmhHWGxn",
        "domain_key": "photos.google.com",
        "emoji": "\U0001f4f7",
        "bg_color": "#34A853",
        "fg_color": "#FFFFFF",
    },
    {
        "id": "aol_news",
        "label": "AOL News",
        "display_name": "AOL News",
        "url": "https://www.aol.com",
        "domain_key": "aol.com",
        "emoji": "\U0001f4f0",
        "bg_color": "#FF5733",
        "fg_color": "#FFFFFF",
    },
    {
        "id": "aol_mail",
        "label": "AOL Mail",
        "display_name": "AOL Mail",
        "url": "https://mail.aol.com",
        "domain_key": "mail.aol.com",
        "emoji": "\u2709\ufe0f",
        "bg_color": "#FF5733",
        "fg_color": "#FFFFFF",
    },
    {
        "id": "desktop",
        "label": "Desktop",
        "display_name": "Windows Desktop",
        "url": "desktop://",
        "domain_key": None,
        "emoji": "\U0001f5a5\ufe0f",
        "bg_color": "#0078D7",
        "fg_color": "#FFFFFF",
    },
]

# Map domain suffixes to friendly display names (longest-match wins)
_DOMAIN_TO_NAME: dict[str, str] = {
    "mail.aol.com": "AOL Mail",
    "photos.google.com": "Milo (Photos)",
    "facebook.com": "Facebook",
    "aol.com": "AOL News",
    "google.com": "Milo (Photos)",
}

# ---------------------------------------------------------------------------
# Greeting
# ---------------------------------------------------------------------------


def get_greeting(hour: int) -> str:
    """
    Return a time-appropriate greeting word for the given 24-hour hour.

    5-11  -> "Good Morning"
    12-16 -> "Good Afternoon"
    17-20 -> "Good Evening"
    21-23 and 0-4 -> "Good Night"
    """
    if 5 <= hour <= 11:
        return "Good Morning"
    elif 12 <= hour <= 16:
        return "Good Afternoon"
    elif 17 <= hour <= 20:
        return "Good Evening"
    else:
        return "Good Night"


def get_full_greeting(hour: int, name: str) -> str:
    """Return the full greeting line, e.g. 'Good Morning, Gertrude!'"""
    return f"{get_greeting(hour)}, {name}!"


# ---------------------------------------------------------------------------
# URL safety
# ---------------------------------------------------------------------------

# Default whitelist used by is_safe_url (module-level convenience)
_DEFAULT_WHITELIST = [
    "facebook.com",
    "photos.google.com",
    "google.com",
    "aol.com",
    "mail.aol.com",
]


def _extract_domain(url: str) -> str | None:
    """Return the netloc (hostname) from a URL, or None on parse failure."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() or None
    except Exception:
        return None


def _domain_in_whitelist(hostname: str, whitelist: list[str]) -> bool:
    """
    Return True if hostname matches or is a subdomain of any entry in whitelist.
    Uses strict suffix matching to avoid lookalike attacks.
    """
    hostname = hostname.lower().lstrip("www.")
    for allowed in whitelist:
        allowed = allowed.lower()
        if hostname == allowed:
            return True
        if hostname.endswith("." + allowed):
            return True
    return False


def is_safe_url(url: str, whitelist: list[str] | None = None) -> bool:
    """
    Return True if url is safe to navigate to.

    Safe means:
    - about:blank
    - file:// (local HTML)
    - The hostname matches or is a subdomain of a whitelisted domain
    """
    if whitelist is None:
        whitelist = _DEFAULT_WHITELIST

    if not url:
        return False

    url_lower = url.lower()

    if url_lower == "about:blank":
        return True

    if url_lower.startswith("file://"):
        return True

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if scheme not in ("http", "https"):
        return False

    hostname = parsed.netloc.lower()
    if not hostname:
        return False

    # Strip port if present
    if ":" in hostname:
        hostname = hostname.split(":")[0]

    # Strip leading www.
    bare = hostname.lstrip("w")  # handles "www." stripping below
    bare = hostname
    if bare.startswith("www."):
        bare = bare[4:]

    return _domain_in_whitelist(bare, whitelist)


# ---------------------------------------------------------------------------
# App display name
# ---------------------------------------------------------------------------


def get_app_display_name(url: str) -> str:
    """
    Return the friendly display name for the app at the given URL.
    Falls back to the hostname or 'Web Page' if unknown.
    """
    if not url:
        return "Web Page"

    # Check desktop pseudo-URL
    if url.startswith("desktop://"):
        return "Windows Desktop"

    try:
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        if hostname.startswith("www."):
            hostname = hostname[4:]
    except Exception:
        return "Web Page"

    # Longest-match: try full hostname first, then progressively shorter
    # e.g. mail.aol.com -> try "mail.aol.com", then "aol.com"
    parts = hostname.split(".")
    for i in range(len(parts)):
        candidate = ".".join(parts[i:])
        if candidate in _DOMAIN_TO_NAME:
            return _DOMAIN_TO_NAME[candidate]

    # Also try APP_REGISTRY by domain_key
    for app in APP_REGISTRY:
        if app["domain_key"] and hostname.endswith(app["domain_key"]):
            return app["display_name"]

    return hostname if hostname else "Web Page"


# ---------------------------------------------------------------------------
# Navigation safety check (richer return value)
# ---------------------------------------------------------------------------


def check_navigation_safety(url: str, whitelist: list[str]) -> dict[str, Any]:
    """
    Check whether navigation to url should be allowed.

    Returns a dict:
        {
            "safe": bool,
            "reason": str,   # human-readable explanation
            "action": str,   # "allow" or "block"
        }
    """
    if not url:
        return {
            "safe": False,
            "reason": "Empty URL is not permitted.",
            "action": "block",
        }

    url_lower = url.lower()

    if url_lower == "about:blank":
        return {"safe": True, "reason": "Built-in blank page.", "action": "allow"}

    if url_lower.startswith("file://"):
        return {
            "safe": True,
            "reason": "Local application file.",
            "action": "allow",
        }

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if scheme not in ("http", "https"):
        return {
            "safe": False,
            "reason": f"URL scheme '{scheme}' is not allowed.",
            "action": "block",
        }

    hostname = parsed.netloc.lower()
    if ":" in hostname:
        hostname = hostname.split(":")[0]

    bare = hostname
    if bare.startswith("www."):
        bare = bare[4:]

    if _domain_in_whitelist(bare, whitelist):
        return {
            "safe": True,
            "reason": f"'{hostname}' is an approved website.",
            "action": "allow",
        }

    return {
        "safe": False,
        "reason": (
            f"'{hostname}' is not on the list of approved websites. "
            "This website has been blocked to keep Gertrude safe."
        ),
        "action": "block",
    }


# ---------------------------------------------------------------------------
# Credential obfuscation (base64 — not encryption, just not plaintext)
# ---------------------------------------------------------------------------


def encode_credential(plaintext: str) -> str:
    """Encode a credential string to a non-plaintext representation."""
    return base64.b64encode(plaintext.encode("utf-8")).decode("ascii")


def decode_credential(encoded: str) -> str:
    """Decode a credential string previously encoded with encode_credential."""
    return base64.b64decode(encoded.encode("ascii")).decode("utf-8")


# ---------------------------------------------------------------------------
# Config load / save
# ---------------------------------------------------------------------------


def load_config(path: str) -> dict[str, Any]:
    """
    Load config from JSON file at path.
    Returns DEFAULT_CONFIG (deep-copied with defaults merged) if file missing or corrupt.
    """
    import copy

    defaults = copy.deepcopy(DEFAULT_CONFIG)

    if not os.path.exists(path):
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge: start from defaults so any missing keys are filled in
        defaults.update(data)
        return defaults
    except (json.JSONDecodeError, OSError):
        return defaults


def save_config(config: dict[str, Any], path: str) -> None:
    """
    Save config dict to JSON file at path.
    Creates the file (and parent directories) if they don't exist.
    """
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Convenience: get app by id
# ---------------------------------------------------------------------------


def get_app_by_id(app_id: str) -> dict[str, Any] | None:
    """Return the app registry entry for the given id, or None."""
    for app in APP_REGISTRY:
        if app["id"] == app_id:
            return app
    return None
