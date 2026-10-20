from pathlib import Path

p = Path("app/api/routes.py")
s = p.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# 1. Pastikan import
# ------------------------------------------------------------
imp = "from app.core.gate_integration import GateIntegration"

if imp not in s:
    anchor = "from app.core.config import settings"
    if anchor not in s:
        raise SystemExit("CONFIG IMPORT NOT FOUND")
    s = s.replace(
        anchor,
        anchor + "\n" + imp,
        1,
    )

# ------------------------------------------------------------
# 2. Pastikan singleton integration
# ------------------------------------------------------------
instance = "_gate_integration = GateIntegration()"

if instance not in s:
    anchor = "_knowledge = KnowledgeEngine()"
    if anchor not in s:
        raise SystemExit("KNOWLEDGE ENGINE MARKER NOT FOUND")
    s = s.replace(
        anchor,
        anchor + "\n" + instance,
        1,
    )

# ------------------------------------------------------------
# 3. Insert Gate 8-13 setelah evidence_text selesai
# ------------------------------------------------------------
if "_gate_integration.process(" not in s:

    marker = """        evidence_text = _build_evidence_text(
            evidence
        )
"""

    if marker not in s:
        raise SystemExit(
            "EVIDENCE TEXT BLOCK NOT FOUND"
        )

    block = """
        # ==========================================================
        # GATE 8-13 LIVE INTEGRATION — SHADOW MODE
        # ==========================================================
        gate_context = _gate_integration.process(
            session_id=request.session_id,
            user_input=request.user_input,
            evidence=evidence,
            intent_name=intent_name,
            intent_confidence=intent_confidence,
            problem=problem,
        )

"""

    s = s.replace(
        marker,
        marker + block,
        1,
    )

# ------------------------------------------------------------
# 4. Simpan response ke Gate 10 Memory
# ------------------------------------------------------------
if "_gate_integration.remember_response(" not in s:

    marker = '        return {'

    if marker not in s:
        raise SystemExit(
            "FINAL RETURN DICT NOT FOUND"
        )

    block = """
        # Store final assistant response in Gate 10 memory.
        _gate_integration.remember_response(
            session_id=request.session_id,
            response=response_text,
        )

"""

    # Hanya target return paling akhir.
    pos = s.rfind(marker)

    if pos < 0:
        raise SystemExit(
            "FINAL RETURN POSITION NOT FOUND"
        )

    s = s[:pos] + block + s[pos:]

# ------------------------------------------------------------
# 5. Expose Gate 8-13 observability
# ------------------------------------------------------------
target = '            "response": response_text,'

if target in s and '"gate_pipeline": gate_context' not in s:
    s = s.replace(
        target,
        target + '\n            "gate_pipeline": gate_context,',
        1,
    )

# ------------------------------------------------------------
# 6. Write
# ------------------------------------------------------------
p.write_text(s, encoding="utf-8")

print("GATE 8-13 ROUTES PATCH : PASS")
print("PROCESS:", "_gate_integration.process(" in s)
print(
    "MEMORY:",
    "_gate_integration.remember_response(" in s,
)
print(
    "OBSERVABILITY:",
    '"gate_pipeline": gate_context' in s,
)
