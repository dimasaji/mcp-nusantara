"""
Human Handoff Schemas.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HandoffLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class HandoffStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class HandoffRequest(BaseModel):
    """Request human handoff."""
    handoff_id: str = Field(..., description="ID handoff")
    reason: str = Field(..., description="Alasan handoff")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context")
    requester_role: str = Field(default="assistant", description="Role peminta")
    level: str = Field(default="normal", description="Tingkat urgensi")
    status: str = Field(default="pending", description="Status")
    created_at: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: Optional[str] = Field(default=None)
    resolved_at: Optional[str] = Field(default=None)
    escalation_count: int = Field(default=0, description="Jumlah escalasi")
    escalated_at: Optional[str] = Field(default=None)
    summary: str = Field(default="", description="Ringkasan")
    suggested_action: Optional[str] = Field(default=None, description="Aksi yang disarankan")
    resolution: Optional[str] = Field(default=None, description="Resolusi akhir")
    note: Optional[str] = Field(default=None, description="Catatan")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tambahan")
