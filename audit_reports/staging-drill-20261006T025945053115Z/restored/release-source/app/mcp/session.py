"""
MCP Session - Sesi untuk berinterasi dengan MCP server.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.mcp.mcp import MCPServer, MCPSession as _MCPSession
from app.mcp.schemas import MCPSessionInfo


class Session:
    """
    Wrapper session MCP untuk penggunaan yang lebih sederhana.
    """

    def __init__(
        self,
        server: MCPServer,
        session_id: Optional[str] = None,
    ):
        self._session = _MCPSession(server, session_id)
        self.session_id = self._session.session_id
        self.server = server

    def call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool melalui session."""
        return self._session.call(tool_name, arguments)

    def list_tools(self) -> list:
        """List tools yang tersedia."""
        return self._session.list_tools()

    def get_info(self) -> MCPSessionInfo:
        """Dapatkan informasi session."""
        return self._session.get_info()

    def close(self) -> bool:
        """Tutup session."""
        return self.server.close_session(self.session_id)


def create_session(server: MCPServer, session_id: Optional[str] = None) -> Session:
    """Buat session baru."""
    return Session(server, session_id)


MCPSession = _MCPSession
