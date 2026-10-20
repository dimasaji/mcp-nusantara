from app.trust.engine import TrustEngine

e = TrustEngine()

cases = [
    ("NO_EVIDENCE", [], "test"),
    ("IRRELEVANT", [{"relevance": 0.1}], "test"),
    ("WEAK", [{"relevance": 0.3}], "test"),
    ("STRONG", [{"relevance": 0.8}], "test"),
    ("MIXED", [{"relevance": 0.9}, {"relevance": 0.1}], "test"),
]

print("=== NUSANTARA PHASE 4 TRUST BASELINE ===")

for name, evidence, claim in cases:
    r = e.evaluate(evidence, claim)

    print(f"\n{name}")
    print("  supports_claim :", r.supports_claim)
    print("  confidence     :", r.confidence)
    print("  risk_level     :", r.risk_level.value)
    print("  requires_human :", r.requires_human)
    print("  details        :", r.details)
