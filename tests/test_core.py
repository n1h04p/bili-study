import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugin"))
import core
import vault


class CoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"BILI_STUDY_DATA": self.tmp.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_dpapi_is_not_plaintext_and_detects_tampering(self):
        value = {"sessdata": "example-secret-only-for-test"}
        vault.save_private("test.dpapi", value)
        p = Path(self.tmp.name) / "test.dpapi"
        self.assertNotIn(value["sessdata"].encode(), p.read_bytes())
        self.assertEqual(vault.load_private("test.dpapi"), value)
        data = bytearray(p.read_bytes())
        data[-1] ^= 1
        p.write_bytes(data)
        with self.assertRaises(OSError):
            vault.load_private("test.dpapi")

    def test_inputs_and_cdn_boundary(self):
        self.assertEqual(core.normalize_bvid("https://www.bilibili.com/video/BV1Mb411e7re?p=2"), "BV1Mb411e7re")
        for url in ("https://evil.test/video/BV1Mb411e7re", "file:///secret", "BVinvalid"):
            with self.assertRaises(core.BiliError):
                core.normalize_bvid(url)
        self.assertTrue(core.transcript_host("https://aisubtitle.hdslb.com/bfs/subtitle/test.json"))
        for url in ("https://hdslb.com.evil.test/", "http://aisubtitle.hdslb.com/", "https://x:pass@hdslb.com/", "https://hdslb.com:8080/"):
            self.assertFalse(core.transcript_host(url))

    def test_cookies_remain_encoded(self):
        self.assertEqual(core.parse_cookies(["SESSDATA=a%2Cb; Path=/; Secure", "DedeUserID=123; Path=/", "other=ignored"]), {"sessdata": "a%2Cb", "dedeuserid": "123"})

    def test_time_window_and_pagination(self):
        seg = [{"from": 0, "to": 10, "text": "first"}, {"from": 10, "to": 20, "text": "second"}, {"from": 20, "to": 30, "text": "third"}]
        a = core.slice_segments(seg, 5, 25, 0, 2)
        self.assertEqual(a["next_offset"], 2)
        b = core.slice_segments(seg, 5, 25, a["next_offset"], 2)
        self.assertEqual(b["segments"], [seg[2]])
        self.assertIsNone(b["next_offset"])
        self.assertEqual(core.slice_segments(seg, 10, 20, 0, 10)["segments"], [seg[1]])

    async def test_errors_never_echo_network_exception_contents(self):
        async def bad():
            raise RuntimeError("SESSDATA=do-not-leak; https://example.test/?ticket=secret")
        result = await core.safe_call(bad)
        self.assertNotIn("do-not-leak", json.dumps(result))
        self.assertNotIn("ticket", json.dumps(result))

    async def test_current_qr_domain_is_supported_and_offsite_is_rejected(self):
        for host in ("passport.bilibili.com", "account.bilibili.com"):
            data = {"url": f"https://{host}/h5/account-h5/auth/scan-web?key=test", "qrcode_key": "test-key"}
            with patch.object(core, "api_get", AsyncMock(return_value=(data, {}))):
                result = await core.login_start()
            self.assertTrue(Path(result["qr_image"]).exists())
        data = {"url": "https://bilibili.com.evil.test/scan", "qrcode_key": "test-key"}
        with patch.object(core, "api_get", AsyncMock(return_value=(data, {}))):
            with self.assertRaises(core.BiliError):
                await core.login_start()

    async def test_login_only_saves_complete_credentials_and_never_returns_them(self):
        vault.save_private("pending.dpapi", {"id": "test", "key": "test-key", "created": __import__("time").time()})
        headers = __import__("httpx").Headers([("set-cookie", "SESSDATA=test-secret; Secure"), ("set-cookie", "bili_jct=test-csrf; Secure"), ("set-cookie", "DedeUserID=123; Secure"), ("set-cookie", "buvid3=test-device; Secure")])
        with patch.object(core, "api_get", AsyncMock(return_value=({"code": 0, "url": "https://example.test/?ticket=secret"}, headers))):
            result = await core.login_poll("test")
        self.assertEqual(result["state"], "ok")
        self.assertNotIn("test-secret", json.dumps(result))
        self.assertNotIn("ticket", json.dumps(result))
        self.assertEqual(vault.load_private("credential.dpapi")["dedeuserid"], "123")
        self.assertFalse((Path(self.tmp.name) / "pending.dpapi").exists())

    async def test_incomplete_login_does_not_replace_account(self):
        vault.save_private("pending.dpapi", {"id": "test", "key": "test-key", "created": __import__("time").time()})
        with patch.object(core, "api_get", AsyncMock(return_value=({"code": 0}, __import__("httpx").Headers()))):
            with self.assertRaises(core.BiliError):
                await core.login_poll("test")
        self.assertIsNone(vault.load_private("credential.dpapi"))

    async def test_page_selection_and_missing_subtitles(self):
        fake = AsyncMock()
        fake.get_info.return_value = {"title": "test", "pages": [{"cid": 111}, {"cid": 222}]}
        fake.get_subtitle.return_value = {"subtitles": []}
        with patch.object(core, "credential", return_value=type("Cred", (), {"dedeuserid": "test"})()), patch.object(core.video, "Video", return_value=fake):
            result = await core.subtitles("BV1Mb411e7re", page=2)
        fake.get_subtitle.assert_awaited_once_with(cid=222)
        self.assertEqual(result["status"], "no_subtitles")
        self.assertNotIn("segments", result)


if __name__ == "__main__":
    unittest.main()
