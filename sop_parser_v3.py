from pathlib import Path
import json
import re
from datetime import datetime

ROOT = Path(".")
OCR = ROOT / "data/knowledge/sop/extracted/CAPIL_02_OCR_IND/CAPIL_02_OCR_IND.txt"
OUT = ROOT / "data/knowledge/sop/parsed/CAPIL-02.v3.parsed.json"

text = OCR.read_text(encoding="utf-8", errors="ignore")

def clean(s):
    s = re.sub(r"\s+", " ", s or "")
    return s.strip(" |:-\t")

def unique(items):
    result = []
    seen = set()
    for item in items:
        item = clean(item)
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result

# ============================================================
# PAGE SPLIT
# ============================================================

pages = re.split(r"(?=PAGE\s+\d+)", text, flags=re.I)

def get_page(n):
    for page in pages:
        if re.search(rf"PAGE\s+{n}\b", page, re.I):
            return page
    return ""

p1 = get_page(1)
p2 = get_page(2)
p3 = get_page(3)

if not p1:
    p1 = text

# ============================================================
# IDENTITY
# ============================================================

m = re.search(r"\bNO\s*SOP\s*:\s*([A-Z0-9\-]+)", p1, re.I)
sop_number = m.group(1).strip() if m else "CAPIL-02"

m = re.search(
    r"TGL\s*TERBIT\s*:\s*([A-Z]+\s+\d{4})",
    p1,
    re.I
)
effective_date = m.group(1).upper() if m else None

m = re.search(
    r"NAMA\s*SOP\s*:\s*(.+?)(?:\n|$)",
    p1,
    re.I
)
title = clean(m.group(1)) if m else None

# ============================================================
# CLASSIFICATION
# ============================================================

service = None
if re.search(r"akta\s+kelahiran", title or text, re.I):
    service = "akta_kelahiran"

channel = []
if re.search(r"online", title or text, re.I):
    channel.append("online")

if re.search(r"rumah\s*sakit|klinik|bidan", title or text, re.I):
    channel.append("rumah_sakit_klinik_bidan")

applicant = ["WNI"] if re.search(r"\bWNI\b", title or text) else []

# ============================================================
# LEGAL BASIS
# ============================================================

patterns = [
    r"Undang-Undang Republik Indonesia Nomor\s+\d+\s+Tahun\s+\d+",
    r"Undang-Undang Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Pemerintah Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Presiden Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Daerah(?: Kota Tangerang)? Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Menteri [A-Za-z ]+ Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Walikota(?: Kota Tangerang)? Nomor\s+\d+\s+Tahun\s+\d+",
]

legal_basis = []

for pattern in patterns:
    for match in re.finditer(pattern, p1, re.I):
        legal_basis.append(clean(match.group(0)))

legal_basis = unique(legal_basis)

# ============================================================
# REQUIREMENTS
# ============================================================

requirement_patterns = [
    r"FC\s*KTP[-\s]?el\s*orang\s*tua",
    r"FC\s*Kartu\s*Keluarga",
    r"FC\s*Buku\s*nikah",
    r"Akta\s*Perkawinan",
    r"SPTJM",
    r"Alamat\s*Email",
    r"Nomor\s*Telepon\s*Kepala\s*Keluarga",
]

requirements = []

for pattern in requirement_patterns:
    for m in re.finditer(pattern, p2, re.I):
        value = clean(m.group(0))

        if value.upper() == "SPTJM":
            value = "SPTJM (sesuai konteks SOP)"

        requirements.append(value)

requirements = unique(requirements)

# ============================================================
# PROCEDURE
# Ambil nomor langkah + teks setelah nomor.
# OCR CAPIL-02 menggunakan nomor 1,2,3 dst.
# ============================================================

procedure = []

procedure_patterns = [
    r"(?m)^\s*(\d{1,2})[\.\)]\s*(.+)$",
    r"(?m)^\s*(\d{1,2})\s+([A-Z][^\n]+)$",
]

for pattern in procedure_patterns:
    for m in re.finditer(pattern, p2 + "\n" + p3):
        number = int(m.group(1))
        value = clean(m.group(2))

        if number <= 30 and len(value) >= 8:
            # Hindari baris tabel yang bukan prosedur
            blocked = [
                "pelaksana",
                "mutu baku",
                "kelengkapan",
                "waktu",
                "output",
                "keterangan",
                "ket",
            ]

            if not any(x in value.lower() for x in blocked):
                procedure.append({
                    "step": number,
                    "activity": value
                })

# deduplicate berdasarkan nomor
proc_map = {}
for item in procedure:
    proc_map[item["step"]] = item["activity"]

procedure = [
    {
        "step": number,
        "activity": proc_map[number]
    }
    for number in sorted(proc_map)
]

# ============================================================
# PROCESSING TIME
# ============================================================

processing_time = unique(
    re.findall(
        r"\b\d+\s*(?:Menit|Jam|Hari\s+Kerja)\b",
        text,
        re.I
    )
)

# ============================================================
# OUTPUT
# ============================================================

outputs = []

for value in [
    "Akta Kelahiran",
    "Kartu Keluarga",
    "KIA"
]:
    if re.search(re.escape(value), text, re.I):
        outputs.append(value)

outputs = unique(outputs)

# ============================================================
# ACTORS
# OCR tabel sering memecah nama aktor.
# Gunakan daftar aktor yang benar-benar muncul.
# ============================================================

actor_patterns = [
    r"RS\s*/?\s*Bidan\s*/?\s*Klinik",
    r"Petugas\s+Akta\s+Kelahiran",
    r"Petugas\s+Layanan",
    r"Operator\s+KIA",
    r"Operator\s+KK",
    r"Operator\s+Dafduk",
    r"Operator\s+Capil",
    r"Kasi\s+Kelahiran",
    r"Kabid\s+Dafduk",
    r"Kabid\s+Capil",
    r"Petugas\s+Arsip",
    r"Pemohon",
]

actors = []

for pattern in actor_patterns:
    for m in re.finditer(pattern, p2 + "\n" + p3, re.I):
        actors.append(clean(m.group(0)))

actors = unique(actors)

# ============================================================
# EQUIPMENT
# ============================================================

equipment_patterns = [
    r"Komputer\s*/?\s*PC",
    r"Printer\s+KIA",
    r"Printer\s+Dokumen",
    r"Kertas\s+A4\s+80\s*gram",
    r"Alat\s+Tulis\s+Kantor",
    r"Buku\s+Register",
]

equipment = []

for pattern in equipment_patterns:
    m = re.search(pattern, p1, re.I)
    if m:
        equipment.append(clean(m.group(0)))

equipment = unique(equipment)

# ============================================================
# QUALIFICATION
# Batasi hanya baris yang benar-benar mengandung kata
# kompetensi/kualifikasi.
# ============================================================

qualification = []

for line in p1.splitlines():
    line = clean(line)

    if not line:
        continue

    if re.search(
        r"Memahami|Memiliki kemampuan|mampu|kompetensi",
        line,
        re.I
    ):
        # Buang potongan tabel yang terlalu rusak
        if len(line) <= 250:
            qualification.append(line)

qualification = unique(qualification)

# ============================================================
# RISKS
# ============================================================

risks = []

for pattern in [
    r"Berkas permohonan terselip",
    r"Jaringan komunikasi data offline",
    r"Alat pencetakan rusak",
    r"Kertas HVS A4 80gr\s*/?\s*blanko KIA tidak tersedia",
]:
    m = re.search(pattern, p1, re.I)
    if m:
        risks.append(clean(m.group(0)))

risks = unique(risks)

# ============================================================
# MITIGATION
# ============================================================

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

# ============================================================
# VALIDATION
# PASS = struktur minimum tersedia.
# BUKAN berarti isi sudah diverifikasi manusia.
# ============================================================

warnings = []

if len(requirements) < 4:
    warnings.append(
        "Persyaratan kurang dari minimum hasil OCR; verifikasi terhadap tabel SOP."
    )

if len(legal_basis) < 3:
    warnings.append(
        "Dasar hukum terlalu sedikit; verifikasi halaman dasar hukum."
    )

if len(procedure) < 5:
    warnings.append(
        "Jumlah prosedur terlalu sedikit; verifikasi tabel prosedur."
    )

if not actors:
    warnings.append(
        "Aktor belum berhasil diekstrak; perlu review tabel pelaksana."
    )

if not outputs:
    warnings.append(
        "Output pelayanan tidak ditemukan."
    )

if not processing_time:
    warnings.append(
        "Waktu pelayanan tidak ditemukan."
    )

validation_status = "REVIEW_REQUIRED" if warnings else "READY_FOR_VALIDATION"

# ============================================================
# FINAL JSON
# ============================================================

result = {
    "schema_version": "3.0",

    "document_type": "SOP_TTE",

    "source": {
        "source_file": "CAPIL_02_(1).pdf",
        "source_status": "official",
        "authority": "official",

        # Jangan menganggap TTE otomatis tervalidasi.
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
        "characters": len(text),
        "ocr_file": str(OCR)
    },

    "validation": {
        "status": validation_status,
        "warnings": warnings
    },

    "parser": {
        "engine": "Nusantara SOP Parser V3",
        "mode": "structured_heuristic",
        "generated_at": datetime.now().isoformat()
    }
}

OUT.parent.mkdir(parents=True, exist_ok=True)

OUT.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("=" * 72)
print("NUSANTARA SOP PARSER V3")
print("=" * 72)
print(f"SOP          : {sop_number}")
print(f"TITLE        : {title}")
print(f"SERVICE      : {service}")
print(f"LEGAL BASIS  : {len(legal_basis)}")
print(f"REQUIREMENTS : {len(requirements)}")
print(f"PROCEDURE    : {len(procedure)}")
print(f"ACTORS       : {len(actors)}")
print(f"TIME         : {processing_time}")
print(f"OUTPUT       : {outputs}")
print(f"EQUIPMENT    : {len(equipment)}")
print(f"QUALIFICATION: {len(qualification)}")
print(f"RISKS        : {len(risks)}")
print(f"MITIGATION   : {len(mitigation)}")
print()
print(f"VALIDATION   : {validation_status}")

for warning in warnings:
    print(f"WARNING      : {warning}")

print()
print(f"JSON         : {OUT}")
print("DATABASE     : NOT TOUCHED")
print("=" * 72)
