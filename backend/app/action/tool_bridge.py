from __future__ import annotations

from .engine import ActionEngine


def build_action_engine(existing_tools=None):
    registry = {}

    for name, function in (existing_tools or {}).items():
        if callable(function):
            registry[str(name)] = function

    return ActionEngine(registry)