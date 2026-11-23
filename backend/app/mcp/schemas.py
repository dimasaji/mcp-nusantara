"""
MCP Protocol Schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MCPTool(BaseModel):
    """Definisi MCP tool."""
    name: str = Field(..., description="Nama tool")
    description: str = Field(..., description="Deskripsi tool")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema input")
    handler: Any = Field(default=None, description="Handler function")
    permissions: List[str] = Field(default_factory=list, description="Daftar permission")


class MCPServerInfo(BaseModel):
    """Informasi server MCP."""
    name: str = Field(..., description="Nama server")
    version: str = Field(..., description="Versi server")
    tool_count: int = Field(default=0, description="Jumlah tool")
    session_count: int = Field(default=0, description="Jumlah sesi aktif")


class MCPSessionInfo(BaseModel):
    """Informasi sesi MCP."""
    session_id: str = Field(..., description="ID sesi")
    server_name: str = Field(default="", description="Nama server")
    server_version: str = Field(default="", description="Versi server")
    active_tools: List[str] = Field(default_factory=list, description="Daftar tool aktif")
    created_at: Optional[str] = Field(default=None, description="Waktu pembuatan")
    updated_at: Optional[str] = Field(default=None, description="Waktu update terakhir")


class MCPError(BaseModel):
    """Error dari MCP."""
    code: str = Field(..., description="Kode error")
    message: str = Field(..., description="Pesan error")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detail tambahan")
