"""Real MCP stdio handshake and tool boundary test; does not access the network."""
import asyncio
import json
import os
from pathlib import Path
import tempfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        params = StdioServerParameters(command=str(root / ".venv/Scripts/python.exe"), args=[str(root / "plugin/server.py")], env={**os.environ, "BILI_STUDY_DATA": tmp, "PYTHONUTF8": "1"})
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as s:
                await s.initialize()
                listed = await s.list_tools()
                names = {t.name for t in listed.tools}
                assert names == {"bili_login_start", "bili_login_poll", "bili_whoami", "bili_mentions", "bili_video_info", "bili_subtitles", "bili_comments", "bili_search", "bili_video_frame"}, names
                for t in listed.tools:
                    assert t.annotations.destructiveHint is False
                result = await s.call_tool("bili_whoami", {})
                assert not result.isError
                payload = result.structuredContent or json.loads(result.content[0].text)
                assert payload == {"logged_in": False}, result
                blocked = await s.call_tool("bili_mentions", {})
                payload = blocked.structuredContent or json.loads(blocked.content[0].text)
                assert "error" in payload
                print("MCP handshake passed; 9 tools; no posting tools; login gate passed.")


asyncio.run(main())
