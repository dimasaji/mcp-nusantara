from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.knowledge.grounding import EvidenceGroundingGuard

print("=" * 70)
print("NUSANTARA GROUNDING - DIRECT GUARD TEST")
print("=" * 70)
print("ROOT:", ROOT)

guard = EvidenceGroundingGuard()

answer = (
    "Untuk mengecek status KTP, pengguna harus melakukan "
    "pemeriksaan status melalui sistem layanan."
)

evidence = (
    "KTP-el adalah dokumen identitas penduduk. "
    "Status pengajuan KTP-el dapat diperiksa melalui "
    "layanan administrasi kependudukan."
)

procedure_claim = guard._contains_procedure_claim(answer)
evidence_procedure = guard._evidence_contains_procedure_claim(evidence)

print("")
print("ANSWER:")
print(answer)

print("")
print("EVIDENCE:")
print(evidence)

print("")
print("CHECK 1 - answer procedure claim")
print("contains_procedure_claim :", procedure_claim)

print("")
print("CHECK 2 - evidence procedure")
print("evidence_contains_procedure_claim :", evidence_procedure)

print("")
print("CHECK 3 - FINAL GUARD")
result = guard.validate(answer, evidence)

print("grounded :", result.grounded)
print("reason   :", result.reason)
print("unsupported:", result.unsupported_sentences)

print("")
print("=" * 70)

if procedure_claim is not True:
    raise SystemExit(
        "FAIL: E2E-002 belum dikenali sebagai procedure claim."
    )

if evidence_procedure is not False:
    raise SystemExit(
        "FAIL: evidence masih dianggap sebagai procedural evidence."
    )

if result.grounded is not False:
    raise SystemExit(
        "FAIL: Guard masih menerima klaim prosedural."
    )

print("DIRECT GUARD TEST: PASS")
print("=" * 70)
