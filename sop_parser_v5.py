from pathlib import Path
import json
import re
from datetime import datetime

ROOT = Path(".")
OCR = ROOT / "data/knowledge/sop/extracted/CAPIL_02_OCR_IND/CAPIL_02_OCR_IND.txt"
OUT = ROOT / "data/knowledge/sop/parsed/CAPIL-02.v5.parsed.json"

text = OCR.read_text(encoding="utf-8", errors="ignore")

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip(" |:-\t")

def unique(items):
    result = []
    seen = set()

    for item in items:
        if isinstance(item, dict):
            key = (
                item.get("step"),
                item.get("activity", "").lower()
            )
        else:
            item = clean(item)
            key = item.lower()

        if key not in seen:
            seen.add(key)
            result.append(item)

    return result

lines = [clean(x) for x in text.splitlines()]
lines = [x for x in lines if x]

# ============================================================
# IDENTITY
# ============================================================

m = re.search(r"NO\s*SOP\s*:\s*([A-Z0-9\-]+)", text, re.I)
sop_number = m.group(1) if m else None

m = re.search(r"TGL\s*TERBIT\s*:\s*([A-Z]+\s+\d{4})", text, re.I)
effective_date = m.group(1).upper() if m else None

m = re.search(r"NAMA\s*SOP\s*:\s*(.+?)(?:\n|$)", text, re.I)
title = clean(m.group(1)) if m else None

# ============================================================
# CLASSIFICATION
# ============================================================

service = "akta_kelahiran" if re.search(
    r"akta\s+kelahiran",
    title or "",
    re.I
) else None

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
        value = clean(m.group(0))
        normalized = re.sub(
            r"undang-undang republik indonesia",
            "undang-undang",
            value,
            flags=re.I
        )
        normalized = re.sub(r"\s+", " ", normalized).lower()

        if normalized not in [
            re.sub(
                r"undang-undang republik indonesia",
                "undang-undang",
                x,
                flags=re.I
            ).lower()
            for x in legal_basis
        ]:
            legal_basis.append(value)

# ============================================================
# REQUIREMENTS
# ============================================================

requirements = []

patterns = [
    r"FC\s*KTP[-\s]?el\s*orang\s*tua",
    r"FC\s*Kartu\s*Keluarga",
    r"FC\s*Buku\s*nikah",
    r"Akta\s*Perkawinan",
    r"SPTJM",
    r"Alamat\s*Email",
    r"Nomor\s*Telepon\s*Kepala\s*Keluarga",
]

for pattern in patterns:
    for m in re.finditer(pattern, text, re.I):
        value = clean(m.group(0))

        if value.upper() == "SPTJM":
            value = "SPTJM (nama/jenis perlu verifikasi)"

        requirements.append(value)

requirements = unique(requirements)

# ============================================================
# PROCEDURE
#
# SANGAT KETAT:
# hanya menerima kalimat yang merupakan AKTIVITAS.
# ============================================================

activity_verbs = [
    "mengisi",
    "memeriksa",
    "memverifikasi",
    "menginput",
    "menarik",
    "penarikan",
    "mengusulkan",
    "memproses",
    "mengajukan",
    "melakukan",
    "mencetak",
    "menerima",
    "mengambil",
    "menyerahkan",
    "menandatangani",
]

forbidden_requirement_terms = [
    "fc ktp",
    "fc kartu keluarga",
    "fc buku nikah",
    "akta perkawinan",
    "sptjm",
    "alamat email",
    "nomor telepon",
    "persyaratan",
    "kelengkapan",
]

def is_valid_activity(value):

    value = clean(value)
    low = value.lower()

    if len(value) < 12:
        return False

    # Jangan pernah memasukkan persyaratan
    if any(term in low for term in forbidden_requirement_terms):
        return False

    # Jangan masukkan metadata tabel
    blocked = [
        "mutu baku",
        "pelaksana",
        "keterangan",
        "output",
        "waktu",
        "kelengkapan",
        "tahun",
        "nomor sop",
    ]

    if any(term in low for term in blocked):
        return False

    # Aktivitas minimal harus mempunyai kata kerja
    return any(
        re.search(r"\b" + re.escape(v) + r"\b", low)
        for v in activity_verbs
    )

procedure = []

# Pola nomor + aktivitas
for i, line in enumerate(lines):

    m = re.match(
        r"^(\d{1,2})[\.\)\-:]?\s+(.+)$",
        line
    )

    if not m:
        continue

    step = int(m.group(1))
    activity = clean(m.group(2))

    if 1 <= step <= 30 and is_valid_activity(activity):
        procedure.append({
            "step": step,
            "activity": activity
        })

# Pola aktivitas tanpa nomor
for line in lines:

    if not is_valid_activity(line):
        continue

    # Jangan duplikasi
    if any(
        x["activity"].lower() == line.lower()
        for x in procedure
    ):
        continue

    procedure.append({
        "step": None,
        "activity": line
    })

# ============================================================
# KNOWN OCR ACTIVITY RECOVERY
#
# Hanya memulihkan aktivitas yang memang ditemukan
# dari teks OCR, bukan membuat isi baru.
# ============================================================

known_patterns = [
    r"Mengisi Data.*Menyerahkan Berkas Persyaratan Lengkap",
    r"Memeriksa berkas.*verifikasi.*validasi",
    r"Menginput data pelaporan kelahiran",
    r"Penarikan Data Permohonan Pelaporan Akta Kelahiran",
    r"Mengusulkan Pengajuan Kartu Keluarga dan KIA",
    r"Memproses Pengajuan Kartu Keluarga dan KIA",
    r"Mengajukan Sertifikasi Elektronik Kartu Keluarga",
    r"Mengajukan Sertifikasi Elektronik Akta Kelahiran",
    r"Memverifikasi Sertifikasi Elektronik Akta Kelahiran",
    r"Melakukan Sertifikasi Elektronik Akta Kelahiran",
    r"Mencetak Akta Kelahiran",
    r"Mencetak KK",
    r"Mencetak KIA",
    r"Menerima Cetakan Akta Kelahiran",
    r"Mengambil Akta Kelahiran dan Kartu Keluarga",
    r"Menerima Akta Kelahiran dan Kartu Keluarga",
]

recovered = []

for pattern in known_patterns:

    m = re.search(
        pattern,
        text,
        re.I | re.S
    )

    if m:
        value = clean(m.group(0))

        if is_valid_activity(value):
            recovered.append(value)

# Gabungkan recovery hanya bila procedure hasil OCR
# belum mendapatkan aktivitas yang sama.
for value in recovered:

    if not any(
        value.lower() == x["activity"].lower()
        for x in procedure
    ):
        procedure.append({
            "step": None,
            "activity": value
        })

# ============================================================
# NORMALIZE PROCEDURE
# ============================================================

procedure = unique(procedure)

# Beri nomor hanya pada item yang belum punya nomor,
# berdasarkan urutan kemunculan.
next_step = 1

existing = {
    x["step"]
    for x in procedure
    if x["step"] is not None
}

for item in procedure:

    if item["step"] is None:

        while next_step in existing:
            next_step += 1

        item["step"] = next_step
        existing.add(next_step)
        next_step += 1

procedure = sorted(
    procedure,
    key=lambda x: x["step"]
)

# ============================================================
# ACTORS
# ============================================================

actor_patterns = [
    r"Rumah\s*Sakit",
    r"RS\s*/?\s*Bidan\s*/?\s*Klinik",
    r"Bidan",
    r"Klinik",
    r"Pemohon",
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
]

actors = []

for pattern in actor_patterns:

    for m in re.finditer(pattern, text, re.I):
        value = clean(m.group(0))

        if len(value) <= 80:
            actors.append(value)

actors = unique(actors)

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
    "KIA",
]:
    if re.search(re.escape(value), text, re.I):
        outputs.append(value)

outputs = unique(outputs)

# ============================================================
# EQUIPMENT
# ============================================================

equipment = []

for pattern in [
    r"Komputer\s*/?\s*PC",
    r"Printer\s+KIA",
    r"Printer\s+Dokumen",
    r"Kertas\s+A4\s+80\s*gram",
    r"Alat\s+Tulis\s+Kantor",
    r"Buku\s+Register",
]:

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
        r"Memahami|Memiliki kemampuan",
        line,
        re.I
    ):
        continue

    # Hindari hasil OCR yang jelas bercampur dengan equipment
    if re.search(
        r"\|\s*Kertas|Alat Tulis Kantor|Buku Register",
        line,
        re.I
    ):
        continue

    if len(line) <= 220:
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
# QUALITY VALIDATION
# ============================================================

warnings = []

# Requirement validation
if len(requirements) < 4:
    warnings.append(
        "REQUIREMENTS_INCOMPLETE"
    )

# Procedure validation
valid_procedure = [
    x for x in procedure
    if is_valid_activity(x["activity"])
]

if len(valid_procedure) < 8:
    warnings.append(
        "PROCEDURE_INCOMPLETE_OR_OCR_TABLE_LOSS"
    )

# Detect suspicious procedure
if any(
    any(
        term in x["activity"].lower()
        for term in forbidden_requirement_terms
    )
    for x in procedure
):
    warnings.append(
        "PROCEDURE_CONTAINS_REQUIREMENT_TEXT"
    )

# Actor
if not actors:
    warnings.append(
        "ACTOR_MAPPING_INCOMPLETE"
    )

# Qualification
if not qualification:
    warnings.append(
        "QUALIFICATION_NOT_EXTRACTED"
    )

# Legal basis
if len(legal_basis) < 5:
    warnings.append(
        "LEGAL_BASIS_INCOMPLETE"
    )

# Source verification remains pending
warnings.append(
    "SOURCE_VERIFICATION_PENDING"
)

# ============================================================
# IMPORTANT:
# V5 TIDAK BOLEH MEMBERIKAN STATUS PASS hanya karena field
# tidak kosong.
# ============================================================

if any(
    x in warnings
    for x in [
        "REQUIREMENTS_INCOMPLETE",
        "PROCEDURE_INCOMPLETE_OR_OCR_TABLE_LOSS",
        "PROCEDURE_CONTAINS_REQUIREMENT_TEXT",
        "ACTOR_MAPPING_INCOMPLETE",
        "LEGAL_BASIS_INCOMPLETE",
    ]
):
    validation_status = "REVIEW_REQUIRED"
else:
    validation_status = "READY_FOR_HUMAN_VALIDATION"

# ============================================================
# RESULT
# ============================================================

result = {

    "schema_version": "5.0",

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

    "procedure": valid_procedure,

    "processing_time": processing_time,

    "outputs": outputs,

    "actors": actors,

    "equipment": equipment,

    "qualification": qualification,

    "risks": risks,

    "mitigation": mitigation,

    "evidence": {
        "pages": 3,
        "characters": len(text),
        "ocr_file": str(OCR)
    },

    "validation": {
        "status": validation_status,
        "warnings": unique(warnings)
    },

    "parser": {
        "engine": "Nusantara SOP Parser V5",
        "mode": "quality_gated_ocr_parser",
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
print("NUSANTARA SOP PARSER V5")
print("=" * 72)
print(f"SOP          : {sop_number}")
print(f"TITLE        : {title}")
print(f"SERVICE      : {service}")
print(f"LEGAL BASIS  : {len(legal_basis)}")
print(f"REQUIREMENTS : {len(requirements)}")
print(f"PROCEDURE    : {len(valid_procedure)}")
print(f"ACTORS       : {len(actors)}")
print(f"TIME         : {processing_time}")
print(f"OUTPUT       : {outputs}")
print(f"EQUIPMENT    : {len(equipment)}")
print(f"QUALIFICATION: {len(qualification)}")
print(f"RISKS        : {len(risks)}")
print(f"MITIGATION   : {len(mitigation)}")
print()
print(f"VALIDATION   : {validation_status}")

for warning in unique(warnings):
    print(f"WARNING      : {warning}")

print()
print(f"JSON         : {OUT}")
print("DATABASE     : NOT TOUCHED")
print("=" * 72)
