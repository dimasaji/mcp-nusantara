from pathlib import Path
import hashlib
import json
import re
import sqlite3
from datetime import datetime

ROOT = Path(__file__).resolve().parent
SOP_DIR = ROOT / "data" / "knowledge" / "sop"
ORIGINAL = SOP_DIR / "original"
EXTRACTED = SOP_DIR / "extracted"
MANIFEST = SOP_DIR / "manifest.json"

EXTRACTED.mkdir(parents=True, exist_ok=True)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, "pypdf belum terpasang"

    try:
        reader = PdfReader(str(path))
        pages = []

        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            text = clean_text(text)

            if text:
                pages.append(
                    f"\n=== PAGE {i} ===\n{text}"
                )

        result = "\n".join(pages).strip()

        if not result:
            return None, "PDF tidak memiliki text layer; kemungkinan scan/image PDF"

        return result, None

    except Exception as e:
        return None, str(e)

def detect_metadata(text, filename):
    sample = text[:15000]

    def find(pattern):
        m = re.search(pattern, sample, re.I | re.M)
        return m.group(1).strip() if m else ""

    nomor = find(r"(?:nomor|no\.?)\s*(?:SOP|:)?\s*([A-Z0-9./_-]+)")
    layanan = find(r"(?:layanan|pelayanan)\s*[:\-]\s*(.+)")
    unit = find(r"(?:unit kerja|unit|bidang|seksi)\s*[:\-]\s*(.+)")

    title = ""

    for pattern in [
        r"(?:judul|nama SOP)\s*[:\-]\s*(.+)",
        r"^\s*(SOP.{5,})$",
    ]:
        m = re.search(pattern, sample, re.I | re.M)
        if m:
            title = m.group(1).strip()
            break

    if not title:
        title = Path(filename).stem.replace("_", " ").replace("-", " ")

    scenario = ""

    lower = sample.lower()

    scenario_map = [
        ("pemula", "pemula"),
        ("hilang", "hilang"),
        ("rusak", "rusak"),
        ("perubahan data", "perubahan_data"),
        ("pindah", "pindah"),
        ("datang", "kedatangan"),
        ("kematian", "kematian"),
        ("kelahiran", "kelahiran"),
        ("perkawinan", "perkawinan"),
        ("perceraian", "perceraian"),
    ]

    for keyword, value in scenario_map:
        if keyword in lower:
            scenario = value
            break

    if not scenario:
        scenario = "umum"

    intent = "procedure"

    if any(x in lower for x in ["persyaratan", "syarat", "dokumen yang diperlukan"]):
        intent = "requirements"
    elif any(x in lower for x in ["berapa lama", "jangka waktu", "waktu penyelesaian"]):
        intent = "service_time"
    elif any(x in lower for x in ["biaya", "tarif", "gratis"]):
        intent = "fee"
    elif any(x in lower for x in ["prosedur", "tahapan", "alur", "mekanisme"]):
        intent = "procedure"

    return {
        "document_type": "SOP_TTE",
        "title": title,
        "nomor_sop": nomor,
        "service": layanan,
        "unit": unit,
        "scenario": scenario,
        "intent": intent,
    }

def main():
    pdfs = sorted(ORIGINAL.glob("*.pdf"))

    print("=" * 72)
    print("NUSANTARA SOP INGESTION ENGINE")
    print("=" * 72)
    print("Folder :", ORIGINAL)
    print("PDF    :", len(pdfs))
    print()

    if not pdfs:
        print("ERROR: Tidak ada PDF di folder original.")
        return

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "root": str(ORIGINAL),
        "documents": []
    }

    success = 0
    failed = 0

    for index, pdf in enumerate(pdfs, 1):

        print(f"[{index}/{len(pdfs)}] {pdf.name}")

        digest = sha256(pdf)
        text, error = extract_pdf(pdf)

        item = {
            "filename": pdf.name,
            "path": str(pdf),
            "sha256": digest,
            "size": pdf.stat().st_size,
            "processed_at": datetime.now().isoformat(),
            "status": "failed" if error else "ok",
            "error": error,
        }

        if error:
            print("  STATUS :", error)
            failed += 1
            manifest["documents"].append(item)
            continue

        metadata = detect_metadata(text, pdf.name)

        extracted_name = pdf.stem + ".md"
        extracted_path = EXTRACTED / extracted_name

        md = f"""---
DOCUMENT_TYPE: SOP_TTE
SOURCE_FILE: {pdf.name}
SOURCE_HASH: {digest}
SOURCE_STATUS: official
AUTHORITY: official
VERIFIED: true
TITLE: {metadata["title"]}
NOMOR_SOP: {metadata["nomor_sop"]}
SERVICE: {metadata["service"]}
UNIT: {metadata["unit"]}
SCENARIO: {metadata["scenario"]}
INTENT: {metadata["intent"]}
INGESTED_AT: {datetime.now().isoformat()}
---

# {metadata["title"]}

## Metadata

- Source: {pdf.name}
- SHA256: {digest}
- Document Type: SOP TTE
- Authority: Official
- Verified: True
- Scenario: {metadata["scenario"]}
- Intent: {metadata["intent"]}

## Isi Dokumen

{text}
"""

        extracted_path.write_text(md, encoding="utf-8")

        item.update(metadata)
        item["extracted_file"] = str(extracted_path)
        item["text_length"] = len(text)

        manifest["documents"].append(item)

        success += 1

        print("  STATUS :", "OK")
        print("  SHA256 :", digest[:20] + "...")
        print("  TITLE  :", metadata["title"])
        print("  SCENARIO:", metadata["scenario"])
        print("  INTENT :", metadata["intent"])

    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print()
    print("=" * 72)
    print("INGESTION SUMMARY")
    print("=" * 72)
    print("TOTAL PDF :", len(pdfs))
    print("SUCCESS   :", success)
    print("FAILED    :", failed)
    print("MANIFEST  :", MANIFEST)
    print("EXTRACTED :", EXTRACTED)
    print("=" * 72)

if __name__ == "__main__":
    main()
