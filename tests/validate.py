"""Dependency-free publication checks; not a Shadowrocket runtime emulator."""

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "YouTube-Web.sgmodule"


class PublicationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = MODULE.read_text()
        rows = [line for line in cls.text.splitlines() if line.startswith("http-response ")]
        assert len(rows) == 1
        _, pattern, *pairs = rows[0].split()
        assert len(pairs) % 2 == 0
        cls.pattern = re.compile(pattern)
        cls.pairs = list(zip(pairs[::2], pairs[1::2]))

    def test_target_urls(self):
        for path in ("/", "/?hl=en", "/watch?v=example", "/youtubei/v1/player?prettyPrint=false",
                     "/youtubei/v1/player/ad_break", "/youtubei/v1/next", "/youtubei/v1/browse"):
            for host in ("www.youtube.com", "m.youtube.com"):
                with self.subTest(host=host, path=path):
                    self.assertIsNotNone(self.pattern.search(f"https://{host}{path}"))

    def test_excluded_urls(self):
        for url in (
            "http://www.youtube.com/watch?v=example",
            "https://www.youtube.com.example.org/watch?v=example",
            "https://example.org/watch?v=example",
            "https://youtubei.googleapis.com/youtubei/v1/player",
            "https://www.youtube.com/s/player/example/base.js",
            "https://www.youtube.com/watchlater",
            "https://www.youtube.com/youtubei/v1/player_extra",
            "https://rr1.googlevideo.com/videoplayback?example=1",
        ):
            with self.subTest(url=url):
                self.assertIsNone(self.pattern.search(url))

    def test_rewrite_preserves_sample_playback_data(self):
        original = {
            "adPlacements": [{"sample": True}], "playerAds": [], "adSlots": [],
            "streamingData": {"formats": [{"url": "https://example.org/video"}]},
            "playabilityStatus": {"status": "OK"},
        }
        body = json.dumps(original)
        for before, after in self.pairs:
            body = body.replace(before, after)
        rewritten = json.loads(body)
        self.assertEqual(rewritten["streamingData"], original["streamingData"])
        self.assertEqual(rewritten["playabilityStatus"], original["playabilityStatus"])
        for key in ("adPlacements", "playerAds", "adSlots"):
            self.assertNotIn(key, rewritten)

    def test_decryption_scope(self):
        hosts = re.findall(r"^hostname\s*=\s*(.*)$", self.text, re.M)
        self.assertEqual(hosts, ["www.youtube.com,m.youtube.com"])
        self.assertNotRegex(self.text, r"(?m)^ca-(?:p12|passphrase)\s*=")
        self.assertNotIn("script-path=", self.text)

    def test_public_files_have_no_embedded_secrets(self):
        paths = [MODULE, ROOT / "README.md", ROOT / "LICENSE", ROOT / ".gitignore", Path(__file__)]
        for path in paths:
            text = path.read_text()
            with self.subTest(path=path.name):
                self.assertNotRegex(text, r"-----BEGIN (?:[A-Z ]*PRIVATE KEY|CERTIFICATE)-----")
                self.assertNotRegex(text, r"(?m)^ca-(?:p12|passphrase)\s*=\s*\S+")
                self.assertNotRegex(text, r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")
                self.assertNotIn("/" + "Users/", text)
                self.assertNotRegex(text, r"[A-Za-z0-9+/]{512,}={0,2}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
