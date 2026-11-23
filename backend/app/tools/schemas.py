"""
Tool Engine Schemas.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Definisi tool."""
    name: str = Field(..., description="Nama tool")
    description: str = Field(..., description="Deskripsi tool")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema untuk input")
    permissions: List[str] = Field(default_factory=list, description="Daftar permission")
    enabled: bool = Field(default=True, description="Apakah tool aktif")


class ToolResult(BaseModel):
    """Hasil eksekusi tool."""
    success: bool = Field(default=False, description="Apakah berhasil")
    tool_name: str = Field(default="", description="Nama tool")
    result: Dict[str, Any] = Field(default_factory=dict, description="Hasil")
    error: Optional[str] = Field(default=None, description="Error jika gagal")
