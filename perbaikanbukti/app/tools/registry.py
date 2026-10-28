from typing import Any

from app.tools.filesystem import FileSystemTool


class ToolRegistry:
    """Registry tool yang dapat digunakan Hermes."""

    def __init__(self, workspace: str):
        self.filesystem = FileSystemTool(workspace)

        self.tools = {
            "read_file": self.filesystem.read_file,
            "list_directory": self.filesystem.list_directory,
            "find_file": self.filesystem.find_file,
        }

    def list_tools(self) -> list[str]:
        return list(self.tools.keys())

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:

        if name not in self.tools:
            raise ValueError(
                f"Tool tidak tersedia: {name}"
            )

        return self.tools[name](**arguments)