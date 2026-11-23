from __future__ import annotations


class ActionEngine:

    VERSION = "11.0.0-explicit-tools"

    def __init__(self, tools=None):
        self.tools = dict(tools or {})

    def register(self, name, function):
        self.tools[name] = function

    def execute(
        self,
        name,
        arguments=None,
        authorized=False,
        requires_authorization=False,
    ):

        arguments = arguments or {}

        if requires_authorization and not authorized:
            return {
                "status": "blocked",
                "action": name,
                "error": "Explicit authorization required.",
            }

        function = self.tools.get(name)

        if function is None:
            return {
                "status": "not_found",
                "action": name,
                "error": "Tool is not registered.",
            }

        try:
            result = function(**arguments)

            return {
                "status": "success",
                "action": name,
                "result": result,
            }

        except Exception as exc:

            return {
                "status": "error",
                "action": name,
                "error": f"{type(exc).__name__}: {exc}",
            }