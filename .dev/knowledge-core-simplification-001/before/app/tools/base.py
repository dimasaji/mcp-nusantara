"""
Tool Engine - Base tool interface and built-in tools.
"""
from __future__ import annotations

import operator
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from app.tools.schemas import ToolResult, ToolDefinition


class ToolError(Exception):
    """Error khusus tool."""
    pass


class BaseTool(ABC):
    """
    Base class untuk semua tool.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Any = None,
        permissions: List[str] = None,
        enabled: Any = True,
        handler: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ):
        self.name = name
        self.description = description
        self._handler = handler
        if callable(input_schema):
            self._handler = input_schema
            self.input_schema = permissions if isinstance(permissions, dict) else {"type": "object"}
            self.permissions = enabled if isinstance(enabled, list) else []
            self.enabled = True
        else:
            self.input_schema = input_schema or {"type": "object"}
            self.permissions = permissions or []
            self.enabled = bool(enabled)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if self._handler is None:
            raise ToolError(f"Tool '{self.name}' tidak memiliki handler")
        return self._handler(input_data)

    def get_schema(self) -> ToolDefinition:
        """Dapatkan definisi tool."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            permissions=self.permissions,
            enabled=self.enabled,
        )


class ToolRegistry:
    """
    Registry untuk semua tool.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> "ToolRegistry":
        """Daftarkan tool."""
        self._tools[tool.name] = tool
        return self

    def unregister(self, name: str) -> bool:
        """Hapus tool dari registry."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[BaseTool]:
        """Dapatkan tool oleh nama."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List semua tool."""
        return [
            tool.get_schema().model_dump()
            for tool in self._tools.values()
            if tool.enabled
        ]

    def tool_exists(self, name: str) -> bool:
        """Cek apakah tool ada."""
        return name in self._tools

    def execute(self, name: str, input_data: Dict[str, Any]) -> ToolResult:
        """Eksekusi tool oleh nama."""
        tool = self._tools.get(name)
        if tool is None:
            raise ToolError(f"Tool '{name}' tidak ditemukan")

        if not tool.enabled:
            raise ToolError(f"Tool '{name}' dinonaktifkan")

        try:
            result = tool.execute(input_data)
            return ToolResult(
                success=True,
                tool_name=name,
                result=result,
            )
        except ToolError as e:
            raise
        except Exception as e:
            raise ToolError(f"Error executing tool '{name}': {e}")


# ---- Built-in Tools ----


class CalculatorTool(BaseTool):
    """
    Tool untuk kalkulasi matematika sederhana.
    """

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Kalkulator matematika sederhana",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide", "power", "sqrt", "abs"],
                        "description": "Operasi matematika",
                    },
                    "a": {"type": "number", "description": "Operand pertama"},
                    "b": {"type": "number", "description": "Operand kedua (untuk operasi biner)"},
                },
                "required": ["operation"],
            },
            permissions=["allow_math"],
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Eksekusi kalkulasi."""
        operation = input_data.get("operation", "add")
        a = input_data.get("a")
        b = input_data.get("b")

        try:
            if operation == "add":
                result = a + b if b is not None else a + a
            elif operation == "subtract":
                result = a - b if b is not None else a - a
            elif operation == "multiply":
                result = a * b if b is not None else a * a
            elif operation == "divide":
                if b == 0:
                    raise ToolError("Pembagian dengan nol")
                result = a / b
            elif operation == "power":
                result = a ** b if b is not None else a ** a
            elif operation == "sqrt":
                if a < 0:
                    raise ToolError("Akar kuadrat dari bilangan negatif")
                result = a ** 0.5
            elif operation == "abs":
                result = abs(a)
            else:
                raise ToolError(f"Operasi tidak dikenal: {operation}")

            return {
                "result": result,
                "operation": operation,
                "operands": {"a": a, "b": b},
            }
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Error kalkulasi: {e}")


class DateTimeTool(BaseTool):
    """
    Tool untuk date dan time operasi.
    """

    def __init__(self):
        super().__init__(
            name="date_time",
            description="Operasi tanggal dan waktu",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["current_time", "parse_date", "add_days", "subtract_days", "difference"],
                        "description": "Aksi date/time",
                    },
                    "date_string": {"type": "string", "description": "String tanggal"},
                    "input_format": {"type": "string", "description": "Format input"},
                    "days": {"type": "integer", "description": "Jumlah hari"},
                    "base_date": {"type": "string", "description": "Tanggal dasar"},
                    "date2": {"type": "string", "description": "Tanggal kedua (untuk difference)"},
                },
                "required": ["action"],
            },
            permissions=["allow_time"],
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Eksekusi operasi date/time."""
        from datetime import datetime, timedelta

        action = input_data.get("action", "current_time")

        if action == "current_time":
            now = datetime.utcnow()
            return {
                "timestamp": now.timestamp(),
                "iso": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "weekday": now.strftime("%A"),
            }

        elif action == "parse_date":
            date_string = input_data.get("date_string", "")
            input_format = input_data.get("input_format", "%Y-%m-%d")
            dt = datetime.strptime(date_string, input_format)
            return {
                "parsed": dt.isoformat(),
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "weekday": dt.strftime("%A"),
            }

        elif action == "add_days":
            base_date = input_data.get("base_date", datetime.utcnow().strftime("%Y-%m-%d"))
            days = input_data.get("days", 1)
            dt = datetime.strptime(base_date, "%Y-%m-%d")
            result = dt + timedelta(days=days)
            return {
                "new_date": result.strftime("%Y-%m-%d"),
                "days_added": days,
                "original_date": base_date,
            }

        elif action == "subtract_days":
            base_date = input_data.get("base_date", datetime.utcnow().strftime("%Y-%m-%d"))
            days = input_data.get("days", 1)
            dt = datetime.strptime(base_date, "%Y-%m-%d")
            result = dt - timedelta(days=days)
            return {
                "new_date": result.strftime("%Y-%m-%d"),
                "days_subtracted": days,
                "original_date": base_date,
            }

        elif action == "difference":
            date1 = input_data.get("base_date", datetime.utcnow().strftime("%Y-%m-%d"))
            date2 = input_data.get("date2", "")
            dt1 = datetime.strptime(date1, "%Y-%m-%d")
            dt2 = datetime.strptime(date2, "%Y-%m-%d")
            diff = abs((dt2 - dt1).days)
            return {
                "difference_days": diff,
                "date1": date1,
                "date2": date2,
            }

        raise ToolError(f"Aksi tidak dikenal: {action}")


_default_registry = ToolRegistry()
_default_registry.register(CalculatorTool())
_default_registry.register(DateTimeTool())


def create_registry() -> ToolRegistry:
    return ToolRegistry()


def get_default_registry() -> ToolRegistry:
    return _default_registry


def execute_calculator(operation: str, a: float, b: float = None) -> Dict[str, Any]:
    """Shortcut kalkulator."""
    registry = get_default_registry()
    result = registry.execute("calculator", {"operation": operation, "a": a, "b": b})
    return result.result


def calculator(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Shortcut kalkulator accept dict input."""
    registry = get_default_registry()
    result = registry.execute("calculator", input_data)
    return result.result


def current_time(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Shortcut current_time."""
    registry = get_default_registry()
    result = registry.execute("date_time", {"action": "current_time"})
    return result.result


def parse_date(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Shortcut parse_date."""
    registry = get_default_registry()
    result = registry.execute("date_time", {"action": "parse_date", **input_data})
    return result.result


def add_days(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Shortcut add_days."""
    registry = get_default_registry()
    result = registry.execute("date_time", {"action": "add_days", **input_data})
    return result.result
