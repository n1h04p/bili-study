import base64
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

import av
import httpx
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugin"))
import core
import frames
import server


class FrameTests(unittest.TestCase):
    def test_source_boundary(self):
        self.assertTrue(frames.media_url_allowed("https://upos.test.bilivideo.com/video.m4s"))
        for url in ("http://x.bilivideo.com/a", "https://bilivideo.com.evil.test/a", "https://127.0.0.1/a", "https://u:p@bilivideo.cn/a", "https://bilivideo.com:8888/a"):
            self.assertFalse(frames.media_url_allowed(url))
        with self.assertRaises(core.BiliError):
            frames.select_stream({"is_drm": True})

    def test_reject_redirects_and_non_range_responses(self):
        for status in (200, 302, 403):
            client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(status, headers={"location": "https://evil.test/"})))
            with self.assertRaises(core.BiliError):
                frames.RangeReader("https://x.bilivideo.com/test", client=client)
            client.close()

    def test_seek_and_decode_real_mp4_over_bounded_ranges(self):
        target = io.BytesIO()
        with av.open(target, "w", format="mp4") as output:
            stream = output.add_stream("mpeg4", rate=10)
            stream.width, stream.height, stream.pix_fmt = 160, 90, "yuv420p"
            for i in range(30):
                image = Image.new("RGB", (160, 90), "red" if i < 10 else "blue")
                for packet in stream.encode(av.VideoFrame.from_image(image)):
                    output.mux(packet)
            for packet in stream.encode():
                output.mux(packet)
        data = target.getvalue()
        requests = []
        def handler(request):
            self.assertNotIn("cookie", request.headers)
            requests.append(request)
            start, end = map(int, request.headers["range"].removeprefix("bytes=").split("-"))
            end = min(end, len(data) - 1)
            return httpx.Response(206, headers={"content-range": f"bytes {start}-{end}/{len(data)}"}, content=data[start:end + 1])
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            with frames.RangeReader("https://x.bilivideo.com/test", client=client) as reader:
                png, actual, size = frames.decode_frame(reader, 1.2, 1600)
        self.assertAlmostEqual(actual, 1.2, places=2)
        self.assertEqual(size, (160, 90))
        pixel = Image.open(io.BytesIO(png)).convert("RGB").getpixel((80, 45))
        self.assertGreater(pixel[2], pixel[0] + 100)
        self.assertGreaterEqual(len(requests), 2)

    def test_byte_budget(self):
        def handler(request):
            a, b = map(int, request.headers["range"].removeprefix("bytes=").split("-"))
            b = min(b, 999)
            return httpx.Response(206, headers={"content-range": f"bytes {a}-{b}/1000"}, content=b"x" * (b - a + 1))
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            with frames.RangeReader("https://x.bilivideo.com/test", client=client, budget=100) as reader:
                with self.assertRaises(core.BiliError):
                    reader.read(200)


class FrameToolTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_returns_image_content_with_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "frame.png"
            Image.new("RGB", (16, 16), "blue").save(png)
            result = {"status": "ok", "actual_seconds": 12.3, "image_path": str(png)}
            with patch.object(core, "safe_call", AsyncMock(return_value=result)):
                content = await server.bili_video_frame("BV1Mb411e7re", 12.3)
            self.assertEqual(json.loads(content[0].text)["actual_seconds"], 12.3)
            self.assertEqual(content[1].type, "image")
            self.assertTrue(base64.b64decode(content[1].data).startswith(b"\x89PNG"))
