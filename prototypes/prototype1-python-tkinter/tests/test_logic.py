"""
Gertrude Shell - Unit Tests (TDD Red Phase)
============================================
These tests are written FIRST before the implementation exists.
They define the expected behavior of shell_logic.py.

Run with:  python -m pytest tests/test_logic.py -v
"""

import sys
import os
import json
import tempfile

# Add parent directory to path so we can import shell_logic
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import shell_logic


# ---------------------------------------------------------------------------
# Tests for get_greeting(hour)
# ---------------------------------------------------------------------------

class TestGetGreeting:
    """Tests for the time-based greeting function."""

    def test_greeting_morning_at_midnight(self):
        """Hour 0 (midnight) should give a Morning greeting."""
        result = shell_logic.get_greeting(0)
        assert "Morning" in result
        assert "Gertrude" in result

    def test_greeting_morning_at_6am(self):
        """Hour 6 should give a Morning greeting."""
        result = shell_logic.get_greeting(6)
        assert "Morning" in result
        assert "Gertrude" in result

    def test_greeting_morning_at_11am(self):
        """Hour 11 (just before noon) should still give Morning greeting."""
        result = shell_logic.get_greeting(11)
        assert "Morning" in result
        assert "Gertrude" in result

    def test_greeting_afternoon_at_noon(self):
        """Hour 12 (noon) should give an Afternoon greeting."""
        result = shell_logic.get_greeting(12)
        assert "Afternoon" in result
        assert "Gertrude" in result

    def test_greeting_afternoon_at_3pm(self):
        """Hour 15 should give an Afternoon greeting."""
        result = shell_logic.get_greeting(15)
        assert "Afternoon" in result
        assert "Gertrude" in result

    def test_greeting_afternoon_at_5pm(self):
        """Hour 17 (5 PM) should still give Afternoon greeting."""
        result = shell_logic.get_greeting(17)
        assert "Afternoon" in result
        assert "Gertrude" in result

    def test_greeting_evening_at_6pm(self):
        """Hour 18 (6 PM) should give an Evening greeting."""
        result = shell_logic.get_greeting(18)
        assert "Evening" in result
        assert "Gertrude" in result

    def test_greeting_evening_at_9pm(self):
        """Hour 21 should give an Evening greeting."""
        result = shell_logic.get_greeting(21)
        assert "Evening" in result
        assert "Gertrude" in result

    def test_greeting_evening_at_11pm(self):
        """Hour 23 should give an Evening greeting."""
        result = shell_logic.get_greeting(23)
        assert "Evening" in result
        assert "Gertrude" in result

    def test_greeting_boundary_morning_to_afternoon(self):
        """Hour 11 = Morning, Hour 12 = Afternoon (strict boundary)."""
        assert "Morning" in shell_logic.get_greeting(11)
        assert "Afternoon" in shell_logic.get_greeting(12)

    def test_greeting_boundary_afternoon_to_evening(self):
        """Hour 17 = Afternoon, Hour 18 = Evening (strict boundary)."""
        assert "Afternoon" in shell_logic.get_greeting(17)
        assert "Evening" in shell_logic.get_greeting(18)


# ---------------------------------------------------------------------------
# Tests for is_safe_url(url)
# ---------------------------------------------------------------------------

class TestIsSafeUrl:
    """Tests for URL whitelist safety checking."""

    def test_facebook_is_safe(self):
        """Facebook URL should be on the whitelist."""
        assert shell_logic.is_safe_url("https://www.facebook.com") is True

    def test_google_photos_is_safe(self):
        """Google Photos URL should be on the whitelist."""
        assert shell_logic.is_safe_url("https://photos.google.com") is True

    def test_aol_news_is_safe(self):
        """AOL main site should be on the whitelist."""
        assert shell_logic.is_safe_url("https://www.aol.com") is True

    def test_aol_mail_is_safe(self):
        """AOL Mail should be on the whitelist."""
        assert shell_logic.is_safe_url("https://mail.aol.com") is True

    def test_random_site_is_not_safe(self):
        """An arbitrary website should NOT pass the whitelist check."""
        assert shell_logic.is_safe_url("https://www.example.com") is False

    def test_empty_string_is_not_safe(self):
        """An empty string should not be considered safe."""
        assert shell_logic.is_safe_url("") is False

    def test_malicious_url_is_not_safe(self):
        """A clearly malicious URL should not pass."""
        assert shell_logic.is_safe_url("https://evil.com/steal-data") is False

    def test_partial_domain_match_is_not_safe(self):
        """A URL that contains a whitelisted domain as a substring is NOT safe."""
        # e.g. "notfacebook.com" should not pass because "facebook" appears in it
        assert shell_logic.is_safe_url("https://notfacebook.com") is False

    def test_subdomain_spoofing_is_not_safe(self):
        """A spoofed subdomain should not be considered safe."""
        assert shell_logic.is_safe_url("https://facebook.com.evil.com") is False

    def test_desktop_special_action_is_safe(self):
        """The special 'desktop' action string should be treated as safe."""
        assert shell_logic.is_safe_url("desktop") is True


# ---------------------------------------------------------------------------
# Tests for get_app_display_name(url)
# ---------------------------------------------------------------------------

class TestGetAppDisplayName:
    """Tests for mapping URLs to friendly display names."""

    def test_facebook_display_name(self):
        assert shell_logic.get_app_display_name("https://www.facebook.com") == "Facebook"

    def test_google_photos_display_name(self):
        result = shell_logic.get_app_display_name("https://photos.google.com")
        assert result == "Milo (Google Photos)"

    def test_aol_news_display_name(self):
        assert shell_logic.get_app_display_name("https://www.aol.com") == "AOL News"

    def test_aol_mail_display_name(self):
        assert shell_logic.get_app_display_name("https://mail.aol.com") == "AOL Mail"

    def test_desktop_display_name(self):
        assert shell_logic.get_app_display_name("desktop") == "Desktop"

    def test_unknown_url_returns_url_itself(self):
        """An unknown URL should return the URL string as a fallback."""
        url = "https://www.unknown.com"
        result = shell_logic.get_app_display_name(url)
        assert result == url


# ---------------------------------------------------------------------------
# Tests for load_config(path) and save_config(config, path)
# ---------------------------------------------------------------------------

class TestConfigIO:
    """Tests for reading and writing the JSON config file."""

    def test_load_config_reads_valid_json(self, tmp_path):
        """load_config should parse a valid JSON file."""
        config_data = {"apps": {"facebook": {"enabled": True}}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        result = shell_logic.load_config(str(config_file))
        assert result == config_data

    def test_load_config_missing_file_returns_default(self, tmp_path):
        """load_config should return a default dict when the file doesn't exist."""
        missing_path = str(tmp_path / "nonexistent.json")
        result = shell_logic.load_config(missing_path)
        assert isinstance(result, dict)
        # Should at least have an 'apps' key in the default
        assert "apps" in result

    def test_load_config_invalid_json_returns_default(self, tmp_path):
        """load_config should return a default dict for malformed JSON."""
        config_file = tmp_path / "bad_config.json"
        config_file.write_text("THIS IS NOT JSON {{{")

        result = shell_logic.load_config(str(config_file))
        assert isinstance(result, dict)
        assert "apps" in result

    def test_save_config_writes_json_file(self, tmp_path):
        """save_config should write a valid JSON file to disk."""
        config_data = {"apps": {"facebook": {"enabled": True}}}
        config_file = str(tmp_path / "output_config.json")

        shell_logic.save_config(config_data, config_file)

        # File must now exist and be valid JSON
        assert os.path.exists(config_file)
        with open(config_file, "r") as f:
            loaded = json.load(f)
        assert loaded == config_data

    def test_save_then_load_roundtrip(self, tmp_path):
        """Data saved by save_config can be reloaded exactly by load_config."""
        original = {
            "apps": {
                "facebook": {"enabled": True, "label": "Facebook"},
                "aol_mail": {"enabled": False, "label": "AOL Mail"},
            },
            "first_run": False,
        }
        config_file = str(tmp_path / "roundtrip.json")
        shell_logic.save_config(original, config_file)
        loaded = shell_logic.load_config(config_file)
        assert loaded == original


# ---------------------------------------------------------------------------
# Tests for get_active_apps(all_apps, config)
# ---------------------------------------------------------------------------

class TestGetActiveApps:
    """Tests for filtering apps based on config enabled/disabled state."""

    # Sample app definition list used across tests
    ALL_APPS = [
        {"key": "facebook",    "label": "Facebook",          "url": "https://www.facebook.com"},
        {"key": "milo",        "label": "Milo (Google Photos)", "url": "https://photos.google.com"},
        {"key": "aol_news",    "label": "AOL News",           "url": "https://www.aol.com"},
        {"key": "aol_mail",    "label": "AOL Mail",           "url": "https://mail.aol.com"},
        {"key": "desktop",     "label": "Desktop",            "url": "desktop"},
    ]

    def test_all_enabled_returns_all(self):
        """When every app is enabled in config, all apps are returned."""
        config = {
            "apps": {app["key"]: {"enabled": True} for app in self.ALL_APPS}
        }
        result = shell_logic.get_active_apps(self.ALL_APPS, config)
        assert len(result) == len(self.ALL_APPS)

    def test_all_disabled_returns_empty(self):
        """When every app is disabled in config, an empty list is returned."""
        config = {
            "apps": {app["key"]: {"enabled": False} for app in self.ALL_APPS}
        }
        result = shell_logic.get_active_apps(self.ALL_APPS, config)
        assert result == []

    def test_only_enabled_apps_returned(self):
        """Only apps whose config 'enabled' flag is True are returned."""
        config = {
            "apps": {
                "facebook":  {"enabled": True},
                "milo":      {"enabled": False},
                "aol_news":  {"enabled": True},
                "aol_mail":  {"enabled": False},
                "desktop":   {"enabled": True},
            }
        }
        result = shell_logic.get_active_apps(self.ALL_APPS, config)
        keys = [app["key"] for app in result]
        assert "facebook" in keys
        assert "aol_news" in keys
        assert "desktop" in keys
        assert "milo" not in keys
        assert "aol_mail" not in keys

    def test_app_missing_from_config_is_excluded(self):
        """If an app has no entry in config at all, it should be excluded."""
        config = {
            "apps": {
                "facebook": {"enabled": True},
                # milo, aol_news, aol_mail, desktop are missing from config
            }
        }
        result = shell_logic.get_active_apps(self.ALL_APPS, config)
        keys = [app["key"] for app in result]
        assert keys == ["facebook"]

    def test_returns_correct_app_objects(self):
        """Returned items should be the original app dicts, not copies with changed data."""
        config = {
            "apps": {
                "facebook": {"enabled": True},
                "milo":     {"enabled": True},
            }
        }
        result = shell_logic.get_active_apps(self.ALL_APPS, config)
        # Both results should be references matching original dicts
        for app in result:
            assert app in self.ALL_APPS


# ---------------------------------------------------------------------------
# Entry point for running tests directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
