"""
TDD Unit Tests for Gertrude Shell Logic
RED phase: write tests first, then implement shell_logic.py

Run with: python -m pytest tests/test_logic.py -v
"""

import json
import os
import sys
import tempfile
import unittest

# Add parent directory so we can import shell_logic
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shell_logic


class TestGetGreeting(unittest.TestCase):
    """Tests for get_greeting(hour) -> str"""

    def test_early_morning(self):
        """Hours 5-11 should return 'Good Morning'"""
        for hour in range(5, 12):
            result = shell_logic.get_greeting(hour)
            self.assertEqual(result, "Good Morning", f"Expected 'Good Morning' for hour {hour}")

    def test_afternoon(self):
        """Hours 12-16 should return 'Good Afternoon'"""
        for hour in range(12, 17):
            result = shell_logic.get_greeting(hour)
            self.assertEqual(result, "Good Afternoon", f"Expected 'Good Afternoon' for hour {hour}")

    def test_evening(self):
        """Hours 17-20 should return 'Good Evening'"""
        for hour in range(17, 21):
            result = shell_logic.get_greeting(hour)
            self.assertEqual(result, "Good Evening", f"Expected 'Good Evening' for hour {hour}")

    def test_night(self):
        """Hours 21-23 and 0-4 should return 'Good Night'"""
        for hour in list(range(21, 24)) + list(range(0, 5)):
            result = shell_logic.get_greeting(hour)
            self.assertEqual(result, "Good Night", f"Expected 'Good Night' for hour {hour}")

    def test_returns_string(self):
        """get_greeting should always return a string"""
        for hour in range(0, 24):
            result = shell_logic.get_greeting(hour)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)


class TestIsSafeUrl(unittest.TestCase):
    """Tests for is_safe_url(url) -> bool"""

    def test_facebook_is_safe(self):
        self.assertTrue(shell_logic.is_safe_url("https://www.facebook.com"))
        self.assertTrue(shell_logic.is_safe_url("https://www.facebook.com/home.php"))
        self.assertTrue(shell_logic.is_safe_url("https://facebook.com"))

    def test_google_photos_is_safe(self):
        self.assertTrue(shell_logic.is_safe_url("https://photos.google.com"))
        self.assertTrue(shell_logic.is_safe_url("https://photos.google.com/albums"))

    def test_aol_is_safe(self):
        self.assertTrue(shell_logic.is_safe_url("https://www.aol.com"))
        self.assertTrue(shell_logic.is_safe_url("https://mail.aol.com"))
        self.assertTrue(shell_logic.is_safe_url("https://mail.aol.com/inbox"))

    def test_unknown_domain_is_not_safe(self):
        # google.com is whitelisted (needed for Google Photos OAuth), so we test
        # other clearly non-whitelisted domains instead.
        self.assertFalse(shell_logic.is_safe_url("https://www.youtube.com"))
        self.assertFalse(shell_logic.is_safe_url("https://www.amazon.com"))
        self.assertFalse(shell_logic.is_safe_url("https://www.example.com"))
        self.assertFalse(shell_logic.is_safe_url("https://www.reddit.com"))

    def test_malicious_lookalike_not_safe(self):
        """Subdomains that look like whitelisted domains but aren't should be blocked"""
        self.assertFalse(shell_logic.is_safe_url("https://evil-facebook.com"))
        self.assertFalse(shell_logic.is_safe_url("https://facebook.com.evil.com"))
        self.assertFalse(shell_logic.is_safe_url("https://notaol.com"))

    def test_empty_url_not_safe(self):
        self.assertFalse(shell_logic.is_safe_url(""))

    def test_about_blank_safe(self):
        """about:blank is a special safe URL"""
        self.assertTrue(shell_logic.is_safe_url("about:blank"))

    def test_local_file_safe(self):
        """Local file:// URLs are safe (our own HTML files)"""
        self.assertTrue(shell_logic.is_safe_url("file:///C:/Users/user/main_board.html"))
        self.assertTrue(shell_logic.is_safe_url("file:///home/user/main_board.html"))

    def test_http_redirected_to_https(self):
        """HTTP versions of whitelisted domains should also be considered safe"""
        self.assertTrue(shell_logic.is_safe_url("http://www.facebook.com"))
        self.assertTrue(shell_logic.is_safe_url("http://mail.aol.com"))


class TestGetAppDisplayName(unittest.TestCase):
    """Tests for get_app_display_name(url) -> str"""

    def test_facebook_display_name(self):
        self.assertEqual(shell_logic.get_app_display_name("https://www.facebook.com"), "Facebook")
        self.assertEqual(shell_logic.get_app_display_name("https://www.facebook.com/home"), "Facebook")

    def test_google_photos_display_name(self):
        self.assertEqual(shell_logic.get_app_display_name("https://photos.google.com"), "Milo (Photos)")
        self.assertEqual(shell_logic.get_app_display_name("https://photos.google.com/albums"), "Milo (Photos)")

    def test_aol_news_display_name(self):
        self.assertEqual(shell_logic.get_app_display_name("https://www.aol.com"), "AOL News")

    def test_aol_mail_display_name(self):
        self.assertEqual(shell_logic.get_app_display_name("https://mail.aol.com"), "AOL Mail")
        self.assertEqual(shell_logic.get_app_display_name("https://mail.aol.com/inbox"), "AOL Mail")

    def test_unknown_url_returns_generic(self):
        result = shell_logic.get_app_display_name("https://www.unknown.com")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_empty_url_returns_generic(self):
        result = shell_logic.get_app_display_name("")
        self.assertIsInstance(result, str)


class TestLoadSaveConfig(unittest.TestCase):
    """Tests for load_config(path) and save_config(config, path)"""

    def setUp(self):
        """Create a temporary directory for test config files"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_config.json")

    def tearDown(self):
        """Clean up temp files"""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.test_dir)

    def test_save_and_load_roundtrip(self):
        """Saving and loading should return the same data"""
        original = {
            "apps_enabled": ["facebook", "milo", "aol_news", "aol_mail"],
            "first_run": False,
            "user_name": "Gertrude"
        }
        shell_logic.save_config(original, self.config_path)
        loaded = shell_logic.load_config(self.config_path)
        self.assertEqual(original["apps_enabled"], loaded["apps_enabled"])
        self.assertEqual(original["first_run"], loaded["first_run"])
        self.assertEqual(original["user_name"], loaded["user_name"])

    def test_load_nonexistent_returns_defaults(self):
        """Loading a missing config should return default config dict"""
        result = shell_logic.load_config("/nonexistent/path/config.json")
        self.assertIsInstance(result, dict)
        self.assertIn("apps_enabled", result)
        self.assertIn("first_run", result)
        self.assertIn("user_name", result)

    def test_save_creates_file(self):
        """save_config should create the file if it doesn't exist"""
        config = {"apps_enabled": [], "first_run": True, "user_name": "Gertrude"}
        shell_logic.save_config(config, self.config_path)
        self.assertTrue(os.path.exists(self.config_path))

    def test_saved_file_is_valid_json(self):
        """The saved config file should be valid JSON"""
        config = {"apps_enabled": ["facebook"], "first_run": False, "user_name": "Gertrude"}
        shell_logic.save_config(config, self.config_path)
        with open(self.config_path, "r") as f:
            loaded_raw = json.load(f)
        self.assertIsInstance(loaded_raw, dict)

    def test_default_config_has_required_keys(self):
        """Default config from load_config must have all required keys"""
        result = shell_logic.load_config("/nonexistent/path.json")
        required_keys = ["apps_enabled", "first_run", "user_name", "whitelist"]
        for key in required_keys:
            self.assertIn(key, result, f"Missing required key: {key}")

    def test_apps_enabled_is_list(self):
        """apps_enabled in default config should be a list"""
        result = shell_logic.load_config("/nonexistent/path.json")
        self.assertIsInstance(result["apps_enabled"], list)

    def test_first_run_is_bool(self):
        """first_run in default config should be a bool"""
        result = shell_logic.load_config("/nonexistent/path.json")
        self.assertIsInstance(result["first_run"], bool)


class TestCredentialObfuscation(unittest.TestCase):
    """Tests for credential encoding/decoding in config"""

    def test_encode_decode_roundtrip(self):
        """Encoding and then decoding should return original string"""
        original = "mypassword123"
        encoded = shell_logic.encode_credential(original)
        decoded = shell_logic.decode_credential(encoded)
        self.assertEqual(original, decoded)

    def test_encoded_is_not_plaintext(self):
        """Encoded credential should not be identical to original"""
        original = "mysecretpassword"
        encoded = shell_logic.encode_credential(original)
        self.assertNotEqual(original, encoded)

    def test_encoded_is_string(self):
        """Encoded credential should be a string"""
        encoded = shell_logic.encode_credential("test")
        self.assertIsInstance(encoded, str)

    def test_empty_string_encode_decode(self):
        """Should handle empty string without error"""
        encoded = shell_logic.encode_credential("")
        decoded = shell_logic.decode_credential(encoded)
        self.assertEqual("", decoded)


class TestCheckNavigationSafety(unittest.TestCase):
    """
    Tests for check_navigation_safety(url, whitelist) -> dict
    Returns: {"safe": bool, "reason": str, "action": str}
    """

    def setUp(self):
        self.whitelist = [
            "facebook.com",
            "photos.google.com",
            "google.com",
            "aol.com",
            "mail.aol.com"
        ]

    def test_safe_url_returns_safe_true(self):
        result = shell_logic.check_navigation_safety(
            "https://www.facebook.com", self.whitelist
        )
        self.assertTrue(result["safe"])

    def test_unsafe_url_returns_safe_false(self):
        result = shell_logic.check_navigation_safety(
            "https://www.evil.com", self.whitelist
        )
        self.assertFalse(result["safe"])

    def test_result_has_required_keys(self):
        """Result dict must have 'safe', 'reason', and 'action' keys"""
        result = shell_logic.check_navigation_safety(
            "https://www.facebook.com", self.whitelist
        )
        self.assertIn("safe", result)
        self.assertIn("reason", result)
        self.assertIn("action", result)

    def test_unsafe_url_has_block_action(self):
        result = shell_logic.check_navigation_safety(
            "https://www.phishing.com", self.whitelist
        )
        self.assertFalse(result["safe"])
        self.assertEqual(result["action"], "block")

    def test_safe_url_has_allow_action(self):
        result = shell_logic.check_navigation_safety(
            "https://www.facebook.com", self.whitelist
        )
        self.assertTrue(result["safe"])
        self.assertEqual(result["action"], "allow")

    def test_local_file_is_always_safe(self):
        result = shell_logic.check_navigation_safety(
            "file:///C:/Users/user/main_board.html", self.whitelist
        )
        self.assertTrue(result["safe"])
        self.assertEqual(result["action"], "allow")

    def test_empty_url_is_blocked(self):
        result = shell_logic.check_navigation_safety("", self.whitelist)
        self.assertFalse(result["safe"])

    def test_reason_is_string(self):
        result = shell_logic.check_navigation_safety(
            "https://www.evil.com", self.whitelist
        )
        self.assertIsInstance(result["reason"], str)
        self.assertGreater(len(result["reason"]), 0)

    def test_custom_whitelist_respected(self):
        """Should use the provided whitelist, not a hardcoded one"""
        custom_whitelist = ["example.com"]
        result_safe = shell_logic.check_navigation_safety(
            "https://www.example.com", custom_whitelist
        )
        result_blocked = shell_logic.check_navigation_safety(
            "https://www.facebook.com", custom_whitelist
        )
        self.assertTrue(result_safe["safe"])
        self.assertFalse(result_blocked["safe"])

    def test_subdomain_of_whitelisted_domain_is_safe(self):
        """Subdomains of whitelisted domains should be allowed"""
        result = shell_logic.check_navigation_safety(
            "https://mail.aol.com/inbox", self.whitelist
        )
        self.assertTrue(result["safe"])

    def test_lookalike_domain_is_blocked(self):
        """Domains that contain but don't end with whitelisted domain should be blocked"""
        result = shell_logic.check_navigation_safety(
            "https://facebook.com.malicious.com", self.whitelist
        )
        self.assertFalse(result["safe"])


class TestGetCurrentGreetingLine(unittest.TestCase):
    """Tests for get_full_greeting(hour, name) -> str"""

    def test_returns_greeting_with_name(self):
        result = shell_logic.get_full_greeting(10, "Gertrude")
        self.assertIn("Gertrude", result)
        self.assertIn("Morning", result)

    def test_includes_time_greeting(self):
        result = shell_logic.get_full_greeting(14, "Gertrude")
        self.assertIn("Afternoon", result)

    def test_returns_string(self):
        result = shell_logic.get_full_greeting(20, "Gertrude")
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
