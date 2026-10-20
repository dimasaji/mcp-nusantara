from pathlib import Path
import json
import re
from datetime import datetime

ROOT = Path(r"C:\Users\dmaza\mcp-starter")

SOURCE = ROOT / "data" / "knowledge" / "sop" / "extracted" / "CAPIL_02_OCR_IND" / "CAPIL_02_OCR_IND.txt"
OUT = ROOT / "data" / "knowledge" / "sop" / "parsed"
OUT.mkdir(parents=True, exist_ok=True)

text = SOURCE.read_text(encoding="utf-8", errors="ignore")

pages = re.split(r"===== HALAMAN \d+ =====", text)
pages = [p.strip() for p in pages if p.strip()]

def clean(s):
    s = re.sub(r"\s+", " ", s or "")
    return s.strip(" :-|")

def unique(items):
    result = []
    seen = set()
    for x in items:
        x = clean(x)
        key = x.lower()
        if x and key not in seen:
            seen.add(key)
            result.append(x)
    return result

def page_text(n):
    return pages[n-1] if len(pages) >= n else ""

# ---------------------------------------------------------
# IDENTITY
# ---------------------------------------------------------

p1 = page_text(1)

m = re.search(r"NO\s*SOP\s*:\s*([A-Z]+[-]\d+)", p1, re.I)
sop_number = m.group(1).upper() if m else "CAPIL-02"

m = re.search(r"TGL\s*TERBIT\s*:\s*([A-Z]+\s+\d{4})", p1, re.I)
effective_date = clean(m.group(1)) if m else None

m = re.search(
    r"NAMA\s*SOP\s*:\s*(Pelayanan Akta Kelahiran.*?WNI)",
    p1,
    re.I
)
title = clean(m.group(1)) if m else None

# ---------------------------------------------------------
# CLASSIFICATION
# ---------------------------------------------------------

service = "akta_kelahiran" if re.search(
    r"akta\s+kelahiran", title or text, re.I
) else None

channel = []
if re.search(r"online", title or text, re.I):
    channel.append("online")
if re.search(r"rumah\s*sakit|klinik|bidan", title or text, re.I):
    channel.append("rumah_sakit_klinik_bidan")

applicant = ["WNI"] if re.search(r"\bWNI\b", title or text) else []

# ---------------------------------------------------------
# LEGAL BASIS
# Ambil hanya pola regulasi, bukan seluruh baris OCR.
# ---------------------------------------------------------

legal_basis = []

patterns = [
    r"Undang-Undang Republik Indonesia Nomor\s+\d+\s+Tahun\s+\d+",
    r"Undang-Undang Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Pemerintah Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Presiden Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Daerah(?: Kota Tangerang)? Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Menteri [A-Za-z ]+ Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Walikota Nomor\s+\d+\s+Tahun\s+\d+",
]

for pattern in patterns:
    legal_basis.extend(re.findall(pattern, p1, re.I))

legal_basis = unique(legal_basis)

# ---------------------------------------------------------
# REQUIREMENTS
# Ambil dari halaman 2 dan bagian yang jelas merupakan
# daftar persyaratan.
# ---------------------------------------------------------

p2 = page_text(2)

requirement_patterns = [
    r"FC\s*KTP[-\s]?el\s*orang\s*tua",
    r"FC\s*Kartu\s*Keluarga",
    r"FC\s*Buku\s*nikah",
    r"Akta\s*Perkawinan",
    r"Surat\s*Pernyataan\s*Tanggung\s*Jawab\s*Mutlak\s*\([^)]+\)",
    r"Alamat\s*Email",
    r"Nomor\s*Telepon\s*Kepala\s*Keluarga",
]

requirements = []

for pattern in requirement_patterns:
    for m in re.finditer(pattern, p2, re.I):
        requirements.append(clean(m.group(0)))

requirements = unique(requirements)

# Tambahkan konteks yang OCR pecah
if re.search(r"SPTJM", p2, re.I):
    requirements.append(
        "SPTJM kebenaran pasangan suami istri"
    )

requirements = unique(requirements)

# ---------------------------------------------------------
# PROCEDURE
# ---------------------------------------------------------

procedure_map = [
    ("Mengisi Data", r"Mengisi Data"),
    ("Memeriksa Berkas", r"Memeriksa berkas"),
    ("Menginput Data Pelaporan Kelahiran", r"Menginput data pelaporan kelahiran"),
    ("Penarikan Data Permohonan", r"Penarikan Data Permohonan"),
    ("Mengusulkan Pengajuan Kartu Keluarga dan KIA",
     r"Mengusulkan.*Kartu Keluarga dan KIA"),
    ("Memproses Pengajuan Kartu Keluarga dan KIA",
     r"Memproses Pengajuan Kartu Keluarga.*KIA"),
    ("Mengajukan Sertifikasi Elektronik Kartu Keluarga",
     r"Mengajukan Sertifikasi Elektronik.*Kartu Keluarga"),
    ("Mengajukan Sertifikasi Elektronik Akta Kelahiran",
     r"Mengajukan Sertifikasi Elektronik.*Akta Kelahiran"),
    ("Memverifikasi Sertifikasi Elektronik Akta Kelahiran",
     r"Memverifikasi Sertifikasi Elektronik.*Akta Kelahiran"),
    ("Melakukan Sertifikasi Elektronik Akta Kelahiran",
     r"Melakukan Sertifikasi Elektronik.*Akta Kelahiran"),
    ("Mencetak Akta Kelahiran", r"Mencetak Akta Kelahiran"),
    ("Mencetak Kartu Keluarga", r"Mencetak KK"),
    ("Mencetak KIA", r"Mencetak KIA"),
    ("Menerima Cetakan Akta Kelahiran dan KK",
     r"Menerima Cetakan Akta Kelahiran"),
    ("Mengambil Akta Kelahiran dan Kartu Keluarga",
     r"Mengambil Akta Kelahiran dan Kartu"),
    ("Menerima Akta Kelahiran dan Kartu Keluarga",
     r"Menerima Akta Kelahiran dan"),
]

procedure = []

for label, pattern in procedure_map:
    if re.search(pattern, text, re.I | re.S):
        procedure.append(label)

# ---------------------------------------------------------
# PROCESSING TIME
# ---------------------------------------------------------

processing_time = unique(
    re.findall(
        r"\b\d+\s*(?:Menit|menit|Jam|jam|Hari Kerja|hari kerja)\b",
        text,
        re.I
    )
)

# ---------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------

outputs = []

for value in [
    "Akta Kelahiran",
    "Kartu Keluarga",
    "KIA"
]:
    if re.search(value, text, re.I):
        outputs.append(value)

# ---------------------------------------------------------
# EQUIPMENT
# ---------------------------------------------------------

equipment = []

for value in [
    "Komputer/ PC",
    "Printer KIA",
    "Printer Dokumen",
    "Kertas A4 80 gram",
    "Alat Tulis Kantor",
    "Buku Register"
]:
    if re.search(re.escape(value), p1, re.I):
        equipment.append(value)

# ---------------------------------------------------------
# QUALIFICATION
# ---------------------------------------------------------

qualification = []

for line in p1.splitlines():
    line = clean(line)

    if re.search(
        r"Memahami|Memiliki kemampuan",
        line,
        re.I
    ):
        qualification.append(line)

qualification = unique(qualification)

# ---------------------------------------------------------
# RISK
# ---------------------------------------------------------

risks = []

risk_patterns = [
    r"Berkas permohonan terselip",
    r"Jaringan komunikasi data offline",
    r"Alat pencetakan rusak",
    r"Kertas HVS A4 80gr.*tidak tersedia",
]

for pattern in risk_patterns:
    m = re.search(pattern, p1, re.I)
    if m:
        risks.append(clean(m.group(0)))

risks = unique(risks)

# ---------------------------------------------------------
# MITIGATION
# ---------------------------------------------------------

mitigation = []

for pattern in [
    r"Melakukan cek kembali berkas permohonan dan data",
    r"Memanfaatkan buku register.*berkas permohonan",
    r"Koordinasi dan konfirmasi jarkomdat.*PIAK PD",
]:
    m = re.search(pattern, p1, re.I)
    if m:
        mitigation.append(clean(m.group(0)))

mitigation = unique(mitigation)

# ---------------------------------------------------------
# ACTORS
# ---------------------------------------------------------

actors = []

for value in [
    "RS/Bidan/Klinik",
    "Petugas Akta Kelahiran",
    "Petugas Layanan",
    "Operator KIA",
    "Operator KK",
    "Operator Dafduk",
    "Operator Capil",
    "Kasi Kelahiran",
    "Kabid Dafduk",
    "Kabid Capil",
    "Petugas Arsip",
]:
    if re.search(re.escape(value), text, re.I):
        actors.append(value)

actors = unique(actors)

# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

warnings = []

if len(requirements) < 5:
    warnings.append(
        "Jumlah persyaratan masih perlu verifikasi terhadap tabel SOP."
    )

if not legal_basis:
    warnings.append("Dasar hukum tidak berhasil diekstrak.")

if not procedure:
    warnings.append("Prosedur tidak berhasil diekstrak.")

if not processing_time:
    warnings.append("Waktu pelayanan tidak ditemukan.")

if not outputs:
    warnings.append("Output pelayanan tidak ditemukan.")

validation_status = "REVIEW_REQUIRED" if warnings else "PASS"

# ---------------------------------------------------------
# FINAL JSON
# ---------------------------------------------------------

result = {
    "schema_version": "2.0",
    "document_type": "SOP_TTE",
    "source": {
        "source_file": "CAPIL_02_(1).pdf",
        "source_status": "official",
        "authority": "official",
        "verification_status": "pending_validation",
        "ocr_engine": "Tesseract 5.4",
        "ocr_language": "ind"
    },

    "identity": {
        "sop_number": sop_number,
        "effective_date": effective_date,
        "title": title
    },

    "classification": {
        "service": service,
        "channel": channel,
        "applicant": applicant
    },

    "legal_basis": legal_basis,

    "requirements": requirements,

    "procedure": procedure,

    "processing_time": processing_time,

    "outputs": outputs,

    "actors": actors,

    "equipment": equipment,

    "qualification": qualification,

    "risks": risks,

    "mitigation": mitigation,

    "evidence": {
        "pages": len(pages),
        "characters": len(text)
    },

    "validation": {
        "status": validation_status,
        "warnings": warnings
    },

    "parser": {
        "engine": "Nusantara SOP Parser V2",
        "mode": "structured_heuristic",
        "generated_at": datetime.now().isoformat()
    }
}

output = OUT / "CAPIL-02.v2.parsed.json"

output.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("=" * 70)
print("NUSANTARA SOP PARSER V2")
print("=" * 70)
print(f"SOP          : {sop_number}")
print(f"TITLE        : {title}")
print(f"SERVICE      : {service}")
print(f"LEGAL BASIS  : {len(legal_basis)}")
print(f"REQUIREMENTS : {len(requirements)}")
print(f"PROCEDURE    : {len(procedure)}")
print(f"TIME         : {processing_time}")
print(f"OUTPUT       : {outputs}")
print(f"ACTORS       : {len(actors)}")
print(f"RISKS        : {len(risks)}")
print(f"MITIGATION   : {len(mitigation)}")
print()
print(f"VALIDATION   : {validation_status}")

for warning in warnings:
    print(f"WARNING      : {warning}")

print()
print(f"JSON         : {output}")
print("DATABASE     : NOT TOUCHED")
print("=" * 70)
