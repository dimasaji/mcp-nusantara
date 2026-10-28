
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import tempfile

from fastapi.testclient import TestClient

from app.main import app
from app.api import routes
from app.hermes.agent import HermesAgent
from app.models.openrouter import OpenRouterProvider
from app.models.cost_ledger import CostLedger


def test_chat_wires_governed_openrouter():
    observed = {}
    original_snapshot = routes.settings.configuration_snapshot
    original_init = HermesAgent.__init__
    original_ledger_init = CostLedger.__init__

    def forced_snapshot():
        configuration, revision = original_snapshot()
        snapshot = configuration._snapshot.model_copy(
            update={
                "llm": configuration.llm.model_copy(
                    update={"provider": "openrouter"}
                )
            }
        )
        return replace(
            configuration,
            _snapshot=snapshot,
        ), revision

    def spy_init(self, *args, **kwargs):
        observed["provider"] = kwargs.get("provider")
        return original_init(self, *args, **kwargs)

    async def fake_execute(self, request, **kwargs):
        raise RuntimeError("ISOLATED_TEST_STOP")

    with tempfile.TemporaryDirectory() as temp:
        def isolated_ledger_init(self, path, **kwargs):
            return original_ledger_init(
                self,
                Path(temp) / "cost.db",
                **kwargs,
            )

        with patch.object(
            type(routes.settings),
            "configuration_snapshot",
            autospec=True,
            side_effect=lambda self: forced_snapshot(),
        ), patch.object(
            CostLedger,
            "__init__",
            isolated_ledger_init,
        ), patch.object(
            HermesAgent,
            "__init__",
            spy_init,
        ), patch.object(
            HermesAgent,
            "execute_v1",
            fake_execute,
        ), patch.object(
            OpenRouterProvider,
            "_key",
            side_effect=AssertionError("EXTERNAL_KEY_ACCESS_FORBIDDEN"),
        ):
            from app.api.routes import ChatRequest
            import asyncio
            from fastapi import HTTPException

            async def diagnose():
                try:
                    await routes.chat(
                        ChatRequest(
                            session_id="isolated-test",
                            user_input="Uji integrasi OpenRouter",
                            stream=False,
                        )
                    )
                except HTTPException as exc:
                    print("HTTP ERROR:", exc.status_code)
                    cause = exc.__cause__
                    if cause is not None:
                        print("ROOT ERROR TYPE:", type(cause).__name__)
                        print("ROOT ERROR:", str(cause)[:1000])
                    else:
                        print("NO CHAINED CAUSE")

            asyncio.run(diagnose())

            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/v1/chat",
                    json={
                        "session_id": "isolated-test",
                        "user_input": "Uji integrasi OpenRouter",
                        "stream": False,
                    },
                )

        provider = observed.get("provider")

        print("HTTP:", response.status_code)
        print("PROVIDER:", type(provider).__name__)

        assert isinstance(provider, OpenRouterProvider)
        assert isinstance(provider._cost_ledger, CostLedger)
        assert callable(provider._cost_estimator)
        assert provider._cost_ledger.path == Path(temp) / "cost.db"

        # Fake Hermes intentionally stops the request.
        assert response.status_code == 500

    print("PASS: HTTP ROUTE -> HERMES -> GOVERNED OPENROUTER")


if __name__ == "__main__":
    test_chat_wires_governed_openrouter()
