import asyncio
import json
import os
import sys

import pytest

pytest.importorskip("mcp", reason="install the project's optional [mcp] dependency")
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_real_stdio_discovery_call_rejection_and_audit(tmp_path):
    async def exercise():
        env = {**os.environ, "NUSANTARA_DATA_DIR": str(tmp_path)}
        params = StdioServerParameters(command=sys.executable,
                                      args=["-m", "app.mcp.stdio_server"], env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert {t.name for t in tools.tools} == {"calculator", "current_time_utc"}
                result = await session.call_tool("calculator", {"expression": "12*3"})
                assert not result.isError
                assert json.loads(result.content[0].text)["result"] == 36
                rejected = await session.call_tool("calculator", {"expression": "__import__('os').getcwd()"})
                assert rejected.isError
                unknown = await session.call_tool("shell", {"command": "whoami"})
                assert unknown.isError
        from app.approval import AuditTrail
        audit = AuditTrail(tmp_path / "audit" / "mcp.jsonl")
        assert audit.verify()
        assert any(e["event"] == "tool.executed" for e in audit.entries())
    await asyncio.wait_for(exercise(), timeout=30)
