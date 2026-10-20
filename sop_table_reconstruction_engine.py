from pathlib import Path
import json
import hashlib
import re
import datetime
import sys

# ============================================================
# NUSANTARA SOP TABLE RECONSTRUCTION ENGINE
# VERSION 1.0
#
# GOVERNANCE PRINCIPLES
# ---------------------
# - Tidak mengubah PDF asli
# - Tidak mengubah OCR evidence
# - Tidak menyentuh Production Knowledge DB
# - Tidak melakukan verifikasi otomatis
# - Tidak mengarang data yang tidak ditemukan
# - Semua hasil reconstruction diberi confidence
# - Evidence koordinat tetap dipertahankan
# ============================================================

ROOT = Path.cwd()

INPUT = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
    / "extracted"
    / "CAPIL_02_GOVERNANCE_OCR"
    / "layout.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
    / "parsed"
    / "CAPIL-02_RECONSTRUCTED"
)

OUTPUT = OUTPUT_DIR / "reconstructed.json"
REPORT = OUTPUT_DIR / "reconstruction_report.json"

ENGINE = "Nusantara SOP Table Reconstruction Engine"
VERSION = "1.0"


# ============================================================
# UTILITY
# ============================================================

def utc_now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def sha256_file(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def clean(value):
    return re.sub(
        r"\s+",
        " ",
        str(value or "")
    ).strip()


def fail(message):
    print()
    print("=" * 78)
    print("RECONSTRUCTION : FAIL-CLOSED")
    print("=" * 78)
    print(message)
    print("=" * 78)
    sys.exit(2)


# ============================================================
# VALIDATE INPUT
# ============================================================

print("=" * 78)
print("NUSANTARA SOP TABLE RECONSTRUCTION ENGINE")
print("=" * 78)
print(f"VERSION : {VERSION}")
print(f"INPUT   : {INPUT}")
print()

if not INPUT.exists():
    fail(
        f"layout.json tidak ditemukan:\n{INPUT}"
    )

try:
    source_hash = sha256_file(INPUT)

    data = json.loads(
        INPUT.read_text(
            encoding="utf-8"
        )
    )

except Exception as exc:
    fail(
        f"Gagal membaca layout.json:\n{exc}"
    )


# ============================================================
# PARAMETERS
# ============================================================

# Vertical tolerance for grouping OCR words into a visual row.
Y_TOLERANCE = 18

# Horizontal gap considered a strong column boundary.
COLUMN_GAP = 45

# Known SOP table headings.
HEADER_TERMS = [
    "no",
    "kegiatan",
    "pelaksana",
    "kelengkapan",
    "waktu",
    "output",
    "mutu baku",
    "persyaratan",
    "peralatan",
]

ACTIVITY_TERMS = [
    "mengisi",
    "memeriksa",
    "memverifikasi",
    "menginput",
    "penarikan",
    "menarik",
    "mengusulkan",
    "memproses",
    "mengajukan",
    "melakukan",
    "mencetak",
    "menerima",
    "mengambil",
    "menandatangani",
    "menyerahkan",
    "memberikan",
    "mengecek",
    "menyiapkan",
]


# ============================================================
# ROW RECONSTRUCTION
# ============================================================

def group_words_into_rows(words):

    words = sorted(
        words,
        key=lambda x: (
            x.get("top", 0),
            x.get("left", 0)
        )
    )

    rows = []

    for word in words:

        top = int(
            word.get("top", 0)
        )

        target = None

        for row in rows:

            if abs(
                top - row["top"]
            ) <= Y_TOLERANCE:

                target = row
                break

        if target is None:

            target = {
                "top": top,
                "words": []
            }

            rows.append(target)

        target["words"].append(word)

    rows.sort(
        key=lambda x: x["top"]
    )

    result = []

    for index, row in enumerate(
        rows,
        start=1
    ):

        row_words = sorted(
            row["words"],
            key=lambda x: x.get(
                "left",
                0
            )
        )

        text = clean(
            " ".join(
                w.get("text", "")
                for w in row_words
            )
        )

        result.append({
            "row": index,
            "top": row["top"],
            "left": min(
                w.get("left", 0)
                for w in row_words
            ),
            "right": max(
                w.get("right", 0)
                for w in row_words
            ),
            "text": text,
            "words": row_words
        })

    return result


# ============================================================
# HEADER DETECTION
# ============================================================

def detect_header(row):

    text = clean(
        row["text"]
    ).lower()

    hits = []

    for term in HEADER_TERMS:

        if term in text:
            hits.append(term)

    return hits


# ============================================================
# COLUMN ESTIMATION
# ============================================================

def estimate_columns(header_row):

    words = header_row["words"]

    columns = []

    for word in words:

        text = clean(
            word.get("text", "")
        )

        if not text:
            continue

        columns.append({
            "label": text,
            "x": word.get("left", 0),
            "right": word.get("right", 0)
        })

    return columns


# ============================================================
# ASSIGN WORDS TO APPROXIMATE COLUMNS
# ============================================================

def assign_columns(row, columns):

    if not columns:
        return []

    result = []

    for word in row["words"]:

        x = word.get(
            "left",
            0
        )

        nearest = min(
            columns,
            key=lambda col: abs(
                x - col["x"]
            )
        )

        result.append({
            "column": nearest["label"],
            "text": word.get("text", ""),
            "x": x,
            "confidence": word.get(
                "confidence",
                -1
            )
        })

    return result


# ============================================================
# ACTIVITY DETECTION
# ============================================================

def activity_score(text):

    normalized = clean(
        text
    ).lower()

    if not normalized:
        return 0.0

    score = 0

    for term in ACTIVITY_TERMS:

        if term in normalized:
            score += 1

    if score >= 2:
        return 1.0

    if score == 1:
        return 0.65

    return 0.0


# ============================================================
# TABLE DETECTION PER PAGE
# ============================================================

all_pages = []

total_rows = 0
candidate_rows = 0
table_headers = []

for page in data.get(
    "pages",
    []
):

    page_number = page.get(
        "page"
    )

    words = page.get(
        "words",
        []
    )

    rows = group_words_into_rows(
        words
    )

    total_rows += len(rows)

    page_headers = []

    for row in rows:

        hits = detect_header(
            row
        )

        if len(hits) >= 2:

            page_headers.append({
                "row": row["row"],
                "top": row["top"],
                "text": row["text"],
                "headers": hits
            })

    if page_headers:

        table_headers.extend(
            [
                {
                    "page": page_number,
                    **header
                }
                for header in page_headers
            ]
        )

    # --------------------------------------------------------
    # Candidate procedural rows
    # --------------------------------------------------------

    candidates = []

    for row in rows:

        text = row["text"]

        score = activity_score(
            text
        )

        if score <= 0:
            continue

        candidate_rows += 1

        candidates.append({
            "page": page_number,
            "row": row["row"],
            "top": row["top"],
            "text": text,
            "activity_score": score,
            "left": row["left"],
            "right": row["right"],
            "words": row["words"]
        })

    # --------------------------------------------------------
    # Detect potential numbered rows
    # --------------------------------------------------------

    numbered = []

    for row in rows:

        match = re.match(
            r"^\s*(\d{1,2})[\.\)\-:]?\s+(.*)",
            row["text"]
        )

        if not match:
            continue

        number = int(
            match.group(1)
        )

        text = clean(
            match.group(2)
        )

        numbered.append({
            "page": page_number,
            "row": row["row"],
            "number": number,
            "text": text,
            "top": row["top"],
            "words": row["words"],
            "activity_score": activity_score(
                text
            )
        })

    # --------------------------------------------------------
    # Page result
    # --------------------------------------------------------

    all_pages.append({
        "page": page_number,
        "rows": rows,
        "table_headers": page_headers,
        "numbered_candidates": numbered,
        "activity_candidates": candidates
    })


# ============================================================
# GLOBAL PROCEDURE CANDIDATES
# ============================================================

numbered_rows = []

for page in all_pages:

    numbered_rows.extend(
        page["numbered_candidates"]
    )

# Deduplicate probable repeated OCR fragments.
unique_numbers = {}

for item in numbered_rows:

    number = item["number"]

    if number not in unique_numbers:

        unique_numbers[number] = item

    else:

        existing = unique_numbers[number]

        # Keep the candidate with stronger activity evidence.
        if (
            item["activity_score"]
            > existing["activity_score"]
        ):
            unique_numbers[number] = item


# ============================================================
# PROCEDURE RECONSTRUCTION
# ============================================================

procedure = []

for number in sorted(
    unique_numbers.keys()
):

    item = unique_numbers[number]

    confidence = item[
        "activity_score"
    ]

    # Do NOT silently claim exact activity.
    # Store reconstructed OCR text as evidence.
    procedure.append({
        "step": number,
        "activity": item["text"],
        "reconstruction_confidence": confidence,
        "evidence": {
            "page": item["page"],
            "row": item["row"],
            "top": item["top"]
        }
    })


# ============================================================
# CONTINUITY ANALYSIS
# ============================================================

if procedure:

    numbers = [
        x["step"]
        for x in procedure
    ]

    min_number = min(numbers)
    max_number = max(numbers)

    expected = set(
        range(
            min_number,
            max_number + 1
        )
    )

    actual = set(numbers)

    missing_steps = sorted(
        expected - actual
    )

else:

    min_number = None
    max_number = None
    missing_steps = []


# ============================================================
# QUALITY GATE
# ============================================================

warnings = []

if not table_headers:

    warnings.append(
        "HEADER_TABEL_TIDAK_TERDETEKSI"
    )

if not procedure:

    warnings.append(
        "PROCEDURE_TIDAK_TERDETEKSI"
    )

if missing_steps:

    warnings.append(
        "NOMOR_PROSEDUR_TIDAK_KONTINU: "
        + ",".join(
            str(x)
            for x in missing_steps
        )
    )

if candidate_rows > 0:

    average_activity_confidence = (
        sum(
            x["reconstruction_confidence"]
            for x in procedure
        )
        / len(procedure)
    )

else:

    average_activity_confidence = 0

if average_activity_confidence < 0.65:

    warnings.append(
        "CONFIDENCE_AKTIVITAS_RENDAH"
    )

# Critical governance rule:
# reconstruction is never automatically verified.

status = (
    "REVIEW_REQUIRED"
    if warnings
    else "READY_FOR_HUMAN_VALIDATION"
)


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

result = {
    "schema_version": "1.0",

    "document_type": "SOP_TTE",

    "governance": {
        "status": status,
        "human_validation_required": True,
        "automatic_verification": False,
        "production_ingestion_allowed": False
    },

    "source": {
        "layout_file": str(
            INPUT.relative_to(ROOT)
        ),
        "layout_sha256": source_hash
    },

    "engine": {
        "name": ENGINE,
        "version": VERSION,
        "generated_at": utc_now()
    },

    "reconstruction": {
        "pages": len(all_pages),
        "total_rows": total_rows,
        "activity_candidate_rows": candidate_rows,
        "table_headers": table_headers,
        "procedure": procedure,
        "missing_steps": missing_steps,
        "average_activity_confidence": round(
            average_activity_confidence,
            3
        )
    },

    "pages": all_pages,

    "warnings": warnings
}

OUTPUT.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

report = {
    "engine": ENGINE,
    "version": VERSION,
    "generated_at": utc_now(),

    "input": {
        "file": str(
            INPUT.relative_to(ROOT)
        ),
        "sha256": source_hash
    },

    "result": {
        "status": status,
        "pages": len(all_pages),
        "rows": total_rows,
        "procedure_candidates": len(
            procedure
        ),
        "missing_steps": missing_steps,
        "warnings": warnings
    },

    "governance": {
        "production_ingestion_allowed": False,
        "automatic_verification": False,
        "human_validation_required": True
    }
}

REPORT.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print()
print("=" * 78)
print("RECONSTRUCTION RESULT")
print("=" * 78)

print(
    f"STATUS                 : {status}"
)

print(
    f"PAGES                  : {len(all_pages)}"
)

print(
    f"ROWS                   : {total_rows}"
)

print(
    f"ACTIVITY CANDIDATES    : {candidate_rows}"
)

print(
    f"PROCEDURE RECONSTRUCTED: {len(procedure)}"
)

print(
    f"MISSING STEPS          : "
    f"{missing_steps if missing_steps else 'NONE'}"
)

print(
    f"AVG ACTIVITY CONF      : "
    f"{average_activity_confidence:.3f}"
)

print()

print("TABLE HEADERS")

if table_headers:

    for header in table_headers:

        print(
            f"  PAGE {header['page']} "
            f"ROW {header['row']} : "
            f"{header['text']}"
        )

else:

    print("  NONE")

print()

print("PROCEDURE CANDIDATES")

for item in procedure:

    print(
        f"  STEP {item['step']:02d} "
        f"[{item['reconstruction_confidence']:.2f}] "
        f"{item['activity']}"
    )

print()

print("WARNINGS")

if warnings:

    for warning in warnings:
        print(
            f"  - {warning}"
        )

else:

    print(
        "  NONE"
    )

print()

print("GOVERNANCE")

print(
    "  Production DB : NOT TOUCHED"
)

print(
    "  Verification  : NOT AUTOMATIC"
)

print(
    "  Human review  : REQUIRED"
)

print()

print(
    f"OUTPUT : {OUTPUT}"
)

print(
    f"REPORT : {REPORT}"
)

print("=" * 78)

sys.exit(0)
