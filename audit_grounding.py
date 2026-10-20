import asyncio
from app.api import routes

class FakeProvider:
    available = True
    model = "audit-fake-model"
    name = "audit-fake-provider"

    def __init__(self, *args, **kwargs):
        self.model = kwargs.get("model") or "audit-fake-model"

    async def health_check(self):
        return {"available": True}

    async def generate(self, req):
        return {
            "content": "KTP-el dikenakan biaya Rp500.000 dan selesai dalam 7 hari.",
            "model": self.model,
            "latency_ms": 1,
        }

    async def close(self):
        pass

class FakeKnowledge:
    def search_knowledge(self, query, top_k=5):
        return [{
            "title": "SOP KTP-el",
            "chunk": "Pelayanan KTP-el dilakukan di loket pelayanan.",
            "score": 0.95,
        }]

async def main():
    original_provider = routes.OllamaProvider
    original_knowledge = routes._knowledge

    routes.OllamaProvider = FakeProvider
    routes._knowledge = FakeKnowledge()

    try:
        request = routes.ChatRequest(
            session_id="grounding-audit",
            user_input="Apa syarat KTP-el yang harus saya bawa?"
        )

        result = await routes.chat(request)

        print("RESPONSE =", result)

    finally:
        routes.OllamaProvider = original_provider
        routes._knowledge = original_knowledge

asyncio.run(main())
