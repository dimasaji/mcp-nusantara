"""Official MCP stdio transport adapting Nusantara's existing governed registry.

Only the two existing read-only builtins are exposed. No shell, filesystem writes,
client-supplied role/permission or alternate policy path.
"""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from app.approval import ApprovalQueue, AuditTrail
from app.governance.mcp_bridge import register_builtin_tools
from app.governance.tools import GovernedToolRegistry


def build_server(data_dir: Path | None = None) -> FastMCP:
    root = data_dir or Path(os.getenv("NUSANTARA_DATA_DIR", "data"))
    registry = GovernedToolRegistry(ApprovalQueue(AuditTrail(root / "audit" / "mcp.jsonl")))
    register_builtin_tools(registry)
    server = FastMCP("nusantara-governed", instructions="Read-only governed Nusantara tools")

    def execute(name: str, arguments: dict) -> dict:
        outcome = registry.execute(name, arguments, role="user", permissions=set(), requested_by="mcp-stdio")
        if outcome.status != "executed":
            # Detailed errors stay in audit; no arbitrary exception content on wire.
            raise ValueError(f"Tool call refused: {outcome.status}")
        return outcome.output

    @server.tool()
    def calculator(expression: str) -> dict:
        """Calculate basic arithmetic without executing code."""
        return execute("calculator", {"expression": expression})

    @server.tool()
    def current_time_utc() -> dict:
        """Return the current UTC timestamp."""
        return execute("current_time_utc", {})

    return server


if __name__ == "__main__":
    build_server().run(transport="stdio")
