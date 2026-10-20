from pathlib import Path
import json
import re
from datetime import datetime

ROOT = Path(".")
OCR = ROOT / "data/knowledge/sop/extracted/CAPIL_02_OCR_IND/CAPIL_02_OCR_IND.txt"
OUT = ROOT / "data/knowledge/sop/parsed/CAPIL-02.v4.parsed.json"

text = OCR.read_text(encoding="utf-8", errors="ignore")

def clean(s):
    s = re.sub(r"\s+", " ", s or "")
    return s.strip(" |:-\t")

def unique(items):
    result = []
    seen = set()

    for item in items:
        if isinstance(item, dict):
            key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        else:
            item = clean(item)
            key = item.lower()

        if key not in seen:
            seen.add(key)
            result.append(item)

    return result

# ============================================================
# NORMALIZE OCR
# ============================================================

lines = [clean(x) for x in text.splitlines()]
lines = [x for x in lines if x]

# ============================================================
# IDENTITY
# ============================================================

m = re.search(
    r"NO\s*SOP\s*:\s*([A-Z0-9\-]+)",
    text,
    re.I
)

sop_number = m.group(1).strip() if m else "CAPIL-02"

m = re.search(
    r"TGL\s*TERBIT\s*:\s*([A-Z]+\s+\d{4})",
    text,
    re.I
)

effective_date = m.group(1).upper() if m else None

m = re.search(
    r"NAMA\s*SOP\s*:\s*(.+?)(?:\n|$)",
    text,
    re.I
)

title = clean(m.group(1)) if m else None

# ============================================================
# CLASSIFICATION
# ============================================================

service = (
    "akta_kelahiran"
    if re.search(r"akta\s+kelahiran", title or text, re.I)
    else None
)

channel = []

if re.search(r"online", title or text, re.I):
    channel.append("online")

if re.search(r"rumah\s*sakit|klinik|bidan", title or text, re.I):
    channel.append("rumah_sakit_klinik_bidan")

applicant = ["WNI"] if re.search(r"\bWNI\b", title or text) else []

# ============================================================
# LEGAL BASIS
# ============================================================

legal_patterns = [
    r"Undang-Undang Republik Indonesia Nomor\s+\d+\s+Tahun\s+\d+",
    r"Undang-Undang Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Pemerintah Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Presiden Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Daerah(?: Kota Tangerang)? Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Menteri [A-Za-z ]+ Nomor\s+\d+\s+Tahun\s+\d+",
    r"Peraturan Walikota(?: Kota Tangerang)? Nomor\s+\d+\s+Tahun\s+\d+",
]

legal_basis = []

for pattern in legal_patterns:
    for m in re.finditer(pattern, text, re.I):
        legal_basis.append(clean(m.group(0)))

# Deduplicate secara lebih kuat berdasarkan jenis + nomor + tahun
legal_unique = []
legal_seen = set()

for item in legal_basis:
    normalized = re.sub(r"\s+", " ", item.lower())
    normalized = normalized.replace(
        "undang-undang republik indonesia",
        "undang-undang"
    )

    key = normalized

    if key not in legal_seen:
        legal_seen.add(key)
        legal_unique.append(item)

legal_basis = legal_unique

# ============================================================
# REQUIREMENTS
# ============================================================

requirements = []

requirement_patterns = [
    r"FC\s*KTP[-\s]?el\s*orang\s*tua",
    r"FC\s*Kartu\s*Keluarga",
    r"FC\s*Buku\s*nikah",
    r"FC\s*Akta\s*Perkawinan",
    r"Akta\s*Perkawinan",
    r"SPTJM",
    r"Alamat\s*Email",
    r"Nomor\s*Telepon\s*Kepala\s*Keluarga",
]

for pattern in requirement_patterns:
    for m in re.finditer(pattern, text, re.I):
        value = clean(m.group(0))

        if value.upper() == "SPTJM":
            value = "SPTJM (sesuai dokumen SOP)"

        requirements.append(value)

requirements = unique(requirements)

# Tambahan berbasis baris OCR jika pola di atas gagal
if len(requirements) < 4:

    for line in lines:

        if re.search(
            r"KTP|Kartu Keluarga|Buku nikah|Perkawinan|SPTJM|Email|Telepon",
            line,
            re.I
        ):

            if len(line) <= 180:
                if not re.search(
                    r"Nama SOP|Kelengkapan|Pelaksana|Output|Waktu",
                    line,
                    re.I
                ):
                    requirements.append(line)

requirements = unique(requirements)

# ============================================================
# PROCEDURE
#
# OCR CAPIL-02 diketahui memiliki langkah 1-18.
# Ambil baris yang diawali nomor.
# ============================================================

procedure_candidates = []

for index, line in enumerate(lines):

    m = re.match(
        r"^(\d{1,2})[\.\)\-:]?\s+(.+)$",
        line
    )

    if not m:
        continue

    number = int(m.group(1))
    activity = clean(m.group(2))

    if number < 1 or number > 30:
        continue

    if len(activity) < 8:
        continue

    # Jangan ambil nomor regulasi, nomor SOP, dsb.
    blocked = [
        "tahun",
        "nomor sop",
        "undang-undang",
        "peraturan",
        "tabel",
        "keterangan",
        "mutu baku",
        "kelengkapan",
    ]

    if any(x in activity.lower() for x in blocked):
        continue

    procedure_candidates.append({
        "step": number,
        "activity": activity
    })

# Jika OCR memisahkan nomor dan aktivitas ke baris berikutnya
for index, line in enumerate(lines[:-1]):

    m = re.match(
        r"^(\d{1,2})$",
        line
    )

    if not m:
        continue

    number = int(m.group(1))

    if number < 1 or number > 30:
        continue

    next_line = lines[index + 1]

    if len(next_line) >= 8:

        blocked = [
            "tahun",
            "nomor sop",
            "pelaksana",
            "mutu baku",
            "keterangan",
        ]

        if not any(x in next_line.lower() for x in blocked):
            procedure_candidates.append({
                "step": number,
                "activity": next_line
            })

# Deduplicate berdasarkan nomor + aktivitas
procedure_candidates = unique(procedure_candidates)

# Ambil satu aktivitas per nomor.
procedure_map = {}

for item in procedure_candidates:

    step = item["step"]
    activity = item["activity"]

    if step not in procedure_map:
        procedure_map[step] = activity

procedure = [
    {
        "step": step,
        "activity": procedure_map[step]
    }
    for step in sorted(procedure_map)
]

# ============================================================
# FALLBACK PROCEDURE
#
# Untuk CAPIL-02 kita sudah melihat isi langkah dari OCR.
# Parser mengambil kalimat aktivitas langsung dari OCR,
# bukan mengarang isi baru.
# ============================================================

if len(procedure) < 5:

    procedure_keywords = [
        "Mengisi Data",
        "Memeriksa berkas",
        "Menginput data pelaporan kelahiran",
        "Penarikan Data Permohonan",
        "Mengusulkan Pengajuan",
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

    fallback = []

    for keyword in procedure_keywords:

        for line in lines:

            if re.search(
                re.escape(keyword),
                line,
                re.I
            ):
                fallback.append(line)
                break

    fallback = unique(fallback)

    procedure = [
        {
            "step": i + 1,
            "activity": value
        }
        for i, value in enumerate(fallback)
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
# OUTPUTS
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
#
# OCR tabel biasanya tidak mempertahankan posisi kolom.
# Ambil nama aktor jika benar-benar muncul.
# ============================================================

actor_patterns = [
    r"RS\s*/?\s*Bidan\s*/?\s*Klinik",
    r"Rumah\s*Sakit",
    r"Bidan",
    r"Klinik",
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

    for m in re.finditer(pattern, text, re.I):
        value = clean(m.group(0))

        if len(value) <= 80:
            actors.append(value)

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

    m = re.search(pattern, text, re.I)

    if m:
        equipment.append(clean(m.group(0)))

equipment = unique(equipment)

# ============================================================
# QUALIFICATION
# ============================================================

qualification = []

for line in lines:

    if not re.search(
        r"Memahami|Memiliki kemampuan|mampu",
        line,
        re.I
    ):
        continue

    # Hindari baris yang jelas merupakan gabungan
    # beberapa kolom tabel OCR.
    if len(line) > 250:
        continue

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

    m = re.search(pattern, text, re.I)

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

    m = re.search(pattern, text, re.I)

    if m:
        mitigation.append(clean(m.group(0)))

mitigation = unique(mitigation)

# ============================================================
# OCR PAGE ESTIMATION
# ============================================================

# Karena OCR script sebelumnya menulis penanda halaman
# dalam bentuk "=== PAGE X ===" atau variasinya,
# hitung secara fleksibel.

page_markers = re.findall(
    r"(?:PAGE|HALAMAN|---\s*PAGE)\s*\d+",
    text,
    re.I
)

page_count = len(set(
    x.lower()
    for x in page_markers
))

if page_count == 0:
    # CAPIL-02 diketahui 3 halaman berdasarkan OCR process.
    # Ini hanya metadata evidence, bukan isi yang dibuat.
    page_count = 3

# ============================================================
# VALIDATION
# ============================================================

warnings = []

if len(requirements) < 4:
    warnings.append(
        "Persyaratan belum cukup untuk ingest produksi."
    )

if len(procedure) < 5:
    warnings.append(
        "Prosedur belum cukup untuk ingest produksi."
    )

if not actors:
    warnings.append(
        "Aktor belum berhasil dipetakan."
    )

if not legal_basis:
    warnings.append(
        "Dasar hukum tidak ditemukan."
    )

if not outputs:
    warnings.append(
        "Output pelayanan tidak ditemukan."
    )

if not processing_time:
    warnings.append(
        "Waktu pelayanan tidak ditemukan."
    )

# Penting:
# walaupun struktur lengkap, provenance/TTE tetap pending.
if not warnings:
    validation_status = "READY_FOR_VALIDATION"
else:
    validation_status = "REVIEW_REQUIRED"

# ============================================================
# FINAL RESULT
# ============================================================

result = {

    "schema_version": "4.0",

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
        "pages": page_count,
        "characters": len(text),
        "ocr_file": str(OCR)
    },

    "validation": {
        "status": validation_status,
        "warnings": warnings
    },

    "parser": {
        "engine": "Nusantara SOP Parser V4",
        "mode": "ocr_tolerant_structured",
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
print("NUSANTARA SOP PARSER V4")
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
