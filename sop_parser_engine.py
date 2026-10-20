from pathlib import Path
import json
import re
from datetime import datetime

ROOT = Path(r"C:\Users\dmaza\mcp-starter")

SOURCE = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
    / "extracted"
    / "CAPIL_02_OCR_IND"
    / "CAPIL_02_OCR_IND.txt"
)

OUT = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
    / "parsed"
)

OUT.mkdir(parents=True, exist_ok=True)

if not SOURCE.exists():
    raise SystemExit(f"Sumber OCR tidak ditemukan:\n{SOURCE}")

text = SOURCE.read_text(
    encoding="utf-8",
    errors="ignore"
)

def clean(value):
    value = re.sub(r"\s+", " ", value or "")
    return value.strip(" :|-")

def first(pattern, flags=re.I):
    m = re.search(pattern, text, flags)
    return clean(m.group(1)) if m else None

# ------------------------------------------------------------
# IDENTITAS SOP
# ------------------------------------------------------------

sop_number = first(
    r"NO\s*SOP\s*[:\-]?\s*([A-Z]+[- ]?\d+)"
)

effective_date = first(
    r"TGL\s*TERBIT\s*[:\-]?\s*([A-Z]+\s+\d{4})"
)

title = first(
    r"NAMA\s*SOP\s*[:\-]?\s*(.+?)(?=\s+Keterkaitan|\n)"
)

# Fallback judul spesifik dari hasil OCR
if not title:
    m = re.search(
        r"NAMA\s*SOP\s*[:\-]?\s*(Pelayanan Akta Kelahiran.+?WNI)",
        text,
        re.I
    )
    if m:
        title = clean(m.group(1))

# ------------------------------------------------------------
# SERVICE
# ------------------------------------------------------------

service = None

if re.search(r"akta\s+kelahiran", text, re.I):
    service = "akta_kelahiran"

elif re.search(r"akta\s+kematian", text, re.I):
    service = "akta_kematian"

elif re.search(r"kartu\s+keluarga", text, re.I):
    service = "kartu_keluarga"

elif re.search(r"KTP[-\s]?el", text, re.I):
    service = "ktp_el"

# ------------------------------------------------------------
# CHANNEL
# ------------------------------------------------------------

channel = []

if re.search(r"online", text, re.I):
    channel.append("online")

if re.search(
    r"rumah\s*sakit|klinik|bidan",
    text,
    re.I
):
    channel.append("rumah_sakit_klinik_bidan")

# ------------------------------------------------------------
# APPLICANT
# ------------------------------------------------------------

applicant = []

if re.search(r"\bWNI\b", text):
    applicant.append("WNI")

# ------------------------------------------------------------
# REQUIREMENTS
# ------------------------------------------------------------

requirements = []

patterns = [
    r"FC\s*KTP[-\s]?el\s*orang\s*tua",
    r"FC\s*Kartu\s*Keluarga",
    r"FC\s*Buku\s*nikah",
    r"Akta\s*Perkawinan",
    r"Surat\s*Pernyataan\s*Tanggung\s*Jawab\s*Mutlak",
    r"Alamat\s*Email",
    r"Nomor\s*Telepon",
]

for pattern in patterns:
    for match in re.finditer(pattern, text, re.I):
        value = clean(match.group(0))
        if value and value not in requirements:
            requirements.append(value)

# ------------------------------------------------------------
# LEGAL BASIS
# ------------------------------------------------------------

legal_basis = []

for match in re.finditer(
    r"(Undang-Undang|Peraturan Presiden|Peraturan Daerah|"
    r"Peraturan Menteri|Peraturan Walikota)[^\n]+",
    text,
    re.I
):
    value = clean(match.group(0))

    if len(value) > 20 and value not in legal_basis:
        legal_basis.append(value)

# ------------------------------------------------------------
# PROCESSING TIME
# ------------------------------------------------------------

processing_times = []

for match in re.finditer(
    r"\b\d+\s*(?:Menit|menit|Jam|jam|Hari Kerja|hari kerja)\b",
    text,
    re.I
):
    value = clean(match.group(0))

    if value not in processing_times:
        processing_times.append(value)

# ------------------------------------------------------------
# OUTPUT DOCUMENTS
# ------------------------------------------------------------

outputs = []

for item in [
    "Akta Kelahiran",
    "Kartu Keluarga",
    "KIA",
]:
    if re.search(item, text, re.I):
        outputs.append(item)

# ------------------------------------------------------------
# PROCEDURE
# ------------------------------------------------------------

procedure_keywords = [
    "Mengisi Data",
    "Memeriksa berkas",
    "Menginput data",
    "Penarikan Data",
    "Mengusulkan",
    "Memproses Pengajuan",
    "Mengajukan Sertifikasi Elektronik",
    "Memverifikasi Sertifikasi Elektronik",
    "Melakukan Sertifikasi Elektronik",
    "Mencetak Akta Kelahiran",
    "Mencetak KK",
    "Mencetak KIA",
    "Menerima Cetakan",
    "Mengambil Akta Kelahiran",
    "Menerima Akta Kelahiran",
]

procedure = []

for keyword in procedure_keywords:
    if re.search(
        re.escape(keyword),
        text,
        re.I
    ):
        procedure.append(keyword)

# ------------------------------------------------------------
# SOURCE / GOVERNANCE
# ------------------------------------------------------------

result = {
    "schema_version": "1.0",
    "document_type": "SOP_TTE",
    "source_file": "CAPIL_02_(1).pdf",
    "source_status": "official",
    "authority": "official",
    "verification_status": "pending_validation",
    "ocr": {
        "engine": "Tesseract",
        "language": "ind",
        "status": "completed",
    },
    "identity": {
        "sop_number": sop_number,
        "effective_date": effective_date,
        "title": title,
    },
    "classification": {
        "service": service,
        "channel": channel,
        "applicant": applicant,
    },
    "requirements": requirements,
    "procedure": procedure,
    "processing_time": processing_times,
    "outputs": outputs,
    "legal_basis": legal_basis,
    "source_text": {
        "characters": len(text),
        "pages": len(
            re.findall(
                r"===== HALAMAN \d+ =====",
                text
            )
        ),
    },
    "parser": {
        "engine": "Nusantara SOP Parser",
        "mode": "heuristic_first_pass",
        "generated_at": datetime.now().isoformat(),
    },
}

# ------------------------------------------------------------
# OUTPUT
# ------------------------------------------------------------

filename = f"{sop_number or 'CAPIL-02'}.parsed.json"
output_file = OUT / filename

output_file.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("=" * 70)
print("NUSANTARA SOP PARSER")
print("=" * 70)
print(f"SOURCE       : {SOURCE}")
print(f"OUTPUT       : {output_file}")
print()
print(f"SOP NUMBER   : {sop_number}")
print(f"TITLE        : {title}")
print(f"SERVICE      : {service}")
print(f"CHANNEL      : {channel}")
print(f"REQUIREMENTS : {len(requirements)}")
print(f"PROCEDURE    : {len(procedure)}")
print(f"TIME         : {processing_times}")
print(f"OUTPUT DOC   : {outputs}")
print(f"LEGAL BASIS  : {len(legal_basis)}")
print()
print("PARSER STATUS: SUCCESS")
print("DATABASE     : NOT TOUCHED")
print("=" * 70)
