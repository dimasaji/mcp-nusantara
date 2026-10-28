from pathlib import Path

p = Path(r".\scripts\test_e2e_grounding_ollama.py")
s = p.read_text(encoding="utf-8")

if "if __name__ == '__main__':" in s or 'if __name__ == "__main__":' in s:
    print("RUNNER sudah ada")
    raise SystemExit(0)

runner = r'''

async def main():
    print("=" * 70)
    print("NUSANTARA AI - E2E GROUNDING + OLLAMA")
    print("=" * 70)
    print("Project :", PROJECT_ROOT)
    print("Model   :", MODEL)

    print()
    print("=" * 70)
    print("OLLAMA HEALTH")
    print("=" * 70)

    try:
        provider = OllamaProvider(model=MODEL)

        health = await provider.health()

        print(health)

        if isinstance(health, dict):
            if not health.get("available", False):
                print("OLLAMA tidak tersedia")
                return 1

    except Exception as exc:
        print("OLLAMA HEALTH ERROR:", exc)
        return 1

    evidence = [
        "KTP-el adalah dokumen identitas penduduk. "
        "Status pengajuan KTP-el dapat diperiksa melalui layanan "
        "administrasi kependudukan.",
        "KTP-el merupakan dokumen identitas penduduk yang diterbitkan "
        "sesuai ketentuan administrasi kependudukan.",
    ]

    cases = [
        (
            "E2E-001",
            "Apa itu KTP-el?",
            True,
        ),
        (
            "E2E-002",
            "Bagaimana cara mengecek status KTP?",
            False,
        ),
        (
            "E2E-003",
            "Apa syarat membuat KTP-el?",
            False,
        ),
    ]

    passed = 0

    for case_id, query, expected in cases:
        result = await run_case(
            case_id,
            query,
            evidence,
            expected,
        )

        if result:
            passed += 1

    total = len(cases)

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(f"{passed}/{total} E2E grounding tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    import asyncio
    raise SystemExit(asyncio.run(main()))
'''

p.write_text(s.rstrip() + runner + "\n", encoding="utf-8")

print("=" * 70)
print("E2E RUNNER RESTORE")
print("=" * 70)
print("PATCH : PASS")
print("FILE  :", p.resolve())
print("RUNNER: restored")
