"""
MCP Server - MCP protocol support.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.mcp.schemas import MCPTool, MCPServerInfo, MCPSessionInfo, MCPError


class MCPServer:
    """
    MCP Server sederhana.
    """

    def __init__(self, name: str = "nusantara-mcp", version: str = "0.1.0"):
        self.name = name
        self.version = version
        self._tools: Dict[str, MCPTool] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, tool: MCPTool = None, **kwargs) -> "MCPServer":
        """Daftarkan MCP tool; mendukung object maupun keyword contract."""
        if tool is None:
            tool = MCPTool(name=kwargs["name"], description=kwargs.get("description", ""), input_schema=kwargs.get("input_schema", {}), handler=kwargs["handler"], permissions=kwargs.get("permissions", []))
        self._tools[tool.name] = tool
        return self

    def get_session_info(self, session_id: str):
        session=self.get_session(session_id)
        if not session: return None
        return {"session_id": session_id, "active_tools": len(self._tools), "active": session.get("active", False)}

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
        permissions: List[str] = None,
    ) -> "MCPServer":
        """Shortcut register tool."""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
            permissions=permissions or [],
        )
        return self.register_tool(tool)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List semua tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "permissions": tool.permissions,
            }
            for tool in self._tools.values()
        ]

    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Dapatkan tool oleh nama."""
        return self._tools.get(name)

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool dengan nama dan arguments."""
        tool = self._tools.get(name)
        if tool is None:
            raise MCPError(f"Tool '{name}' tidak ditemukan")

        try:
            result = tool.handler(arguments)
            return result
        except Exception as e:
            raise MCPError(f"Error calling tool '{name}': {e}")

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Buat sesi baru."""
        if session_id is None:
            session_id = uuid.uuid4().hex[:12]
        self._sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "tools": list(self._tools.keys()),
            "active": True,
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Dapatkan informasi sesi."""
        session = self._sessions.get(session_id)
        if session and session.get("active"):
            return session
        return None

    def close_session(self, session_id: str) -> bool:
        """Tutup sesi."""
        if session_id in self._sessions:
            self._sessions[session_id]["active"] = False
            return True
        return False

    def get_info(self) -> MCPServerInfo:
        """Dapatkan informasi server."""
        return MCPServerInfo(
            name=self.name,
            version=self.version,
            tool_count=len(self._tools),
            session_count=sum(1 for s in self._sessions.values() if s.get("active")),
        )


class MCPSession:
    """
    Sesi MCP untuk berinteraksi dengan server.
    """

    def __init__(self, server: MCPServer, session_id: Optional[str] = None):
        self.server = server
        self.session_id = server.create_session(session_id)
        self._initialize_session()

    def _initialize_session(self):
        """Inisialisasi sesi."""
        pass

    def call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool dalam sesi ini."""
        return self.server.call_tool(tool_name, arguments)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List tools yang tersedia."""
        return self.server.list_tools()

    def get_info(self) -> MCPSessionInfo:
        """Dapatkan informasi sesi."""
        session = self.server.get_session(self.session_id)
        if session:
            return MCPSessionInfo(
                session_id=self.session_id,
                server_name=self.server.name,
                server_version=self.server.version,
                active_tools=session.get("tools", []),
                created_at=session.get("created_at"),
            )
        return MCPSessionInfo(
            session_id=self.session_id,
            server_name=self.server.name,
            server_version=self.server.version,
            active_tools=[],
            created_at=None,
        )


_default_server = MCPServer()


def create_server(name: str = "nusantara-mcp") -> MCPServer:
    """Buat MCP server baru."""
    return MCPServer(name=name)


def get_default_server() -> MCPServer:
    """Dapatkan default MCP server."""
    return _default_server
