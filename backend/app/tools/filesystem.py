from pathlib import Path
from typing import Any


class FileSystemTool:
    """Read-only filesystem tools for Hermes."""

    def __init__(self, workspace: str):
        self.workspace = Path(workspace).resolve()

    def _safe_path(self, path: str) -> Path:
        target = (self.workspace / path).resolve()

        try:
            target.relative_to(self.workspace)
        except ValueError:
            raise PermissionError(
                f"Path di luar workspace tidak diizinkan: {path}"
            )

        return target

    def read_file(self, path: str) -> dict[str, Any]:
        target = self._safe_path(path)

        if not target.exists():
            return {
                "success": False,
                "error": f"File tidak ditemukan: {path}",
            }

        if not target.is_file():
            return {
                "success": False,
                "error": f"Bukan file: {path}",
            }

        content = target.read_text(
            encoding="utf-8",
            errors="replace",
        )

        return {
            "success": True,
            "path": str(target.relative_to(self.workspace)),
            "content": content,
            "size": target.stat().st_size,
        }

    def list_directory(self, path: str = ".") -> dict[str, Any]:
        target = self._safe_path(path)

        if not target.exists():
            return {
                "success": False,
                "error": f"Folder tidak ditemukan: {path}",
            }

        if not target.is_dir():
            return {
                "success": False,
                "error": f"Bukan folder: {path}",
            }

        items = []

        for item in sorted(
            target.iterdir(),
            key=lambda x: x.name.lower()
        ):
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
            })

        return {
            "success": True,
            "path": str(target.relative_to(self.workspace)),
            "items": items,
        }

    def find_file(self, name: str) -> dict[str, Any]:
        matches = []

        for item in self.workspace.rglob(name):
            if item.is_file():
                matches.append(
                    str(item.relative_to(self.workspace))
                )

        return {
            "success": True,
            "query": name,
            "matches": matches[:100],
            "total": len(matches),
        }