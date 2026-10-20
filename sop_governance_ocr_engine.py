from pathlib import Path
import json
import hashlib
import subprocess
import shutil
import sys
import datetime
import tempfile
import re

# ============================================================
# NUSANTARA GOVERNANCE SOP OCR ENGINE
# Version 2.0
#
# PURPOSE:
#   Governance-grade OCR acquisition for signed TTE SOP PDFs.
#
# PRINCIPLES:
#   1. Original PDF is READ-ONLY.
#   2. Production Knowledge DB is NEVER touched.
#   3. Every artifact has SHA-256.
#   4. OCR provenance is recorded.
#   5. Page boundaries are preserved.
#   6. OCR confidence is recorded.
#   7. Coordinate data is preserved.
#   8. Fail-closed on processing errors.
#   9. Human validation remains mandatory.
#  10. No document is automatically marked verified.
# ============================================================

ROOT = Path.cwd()

PDF = ROOT / "data" / "knowledge" / "sop" / "original" / "CAPIL_02_(1).pdf"

OUT = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
    / "extracted"
    / "CAPIL_02_GOVERNANCE_OCR"
)

MANIFEST = OUT / "governance_manifest.json"
LAYOUT = OUT / "layout.json"
TEXT = OUT / "ocr.txt"
REPORT = OUT / "governance_report.json"

TESSERACT = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

TESSDATA = TESSERACT.parent / "tessdata"

VERSION = "2.0"

# ============================================================
# UTILITY
# ============================================================

def utc_now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def sha256_file(path: Path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            block = f.read(1024 * 1024)

            if not block:
                break

            h.update(block)

    return h.hexdigest()


def safe_text(value):
    return re.sub(
        r"\s+",
        " ",
        str(value or "")
    ).strip()


def fail(message, code=1):
    print()
    print("=" * 78)
    print("GOVERNANCE OCR ENGINE : FAIL-CLOSED")
    print("=" * 78)
    print(message)
    print("=" * 78)
    sys.exit(code)


# ============================================================
# ENVIRONMENT VALIDATION
# ============================================================

print("=" * 78)
print("NUSANTARA GOVERNANCE SOP OCR ENGINE")
print("=" * 78)
print(f"ENGINE VERSION : {VERSION}")
print(f"ROOT           : {ROOT}")
print(f"PDF            : {PDF}")
print(f"TESSERACT      : {TESSERACT}")
print(f"OUTPUT         : {OUT}")
print()

if not PDF.exists():
    fail(
        f"PDF sumber tidak ditemukan:\n{PDF}"
    )

if not TESSERACT.exists():
    fail(
        "Tesseract tidak ditemukan.\n"
        f"Expected:\n{TESSERACT}"
    )

if not TESSDATA.exists():
    fail(
        "Folder tessdata tidak ditemukan.\n"
        f"Expected:\n{TESSDATA}"
    )

# ------------------------------------------------------------
# Check language ind
# ------------------------------------------------------------

ind_model = TESSDATA / "ind.traineddata"

if not ind_model.exists():
    fail(
        "Model bahasa Indonesia Tesseract tidak ditemukan.\n"
        f"Expected:\n{ind_model}"
    )

# ------------------------------------------------------------
# Check PDF rendering capability
# ------------------------------------------------------------

try:
    import fitz
except Exception as exc:
    fail(
        "PyMuPDF/fitz belum tersedia.\n"
        "Install dengan:\n"
        "python -m pip install PyMuPDF\n\n"
        f"DETAIL: {exc}"
    )

# ============================================================
# CREATE OUTPUT
# ============================================================

OUT.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# SOURCE HASH
# ============================================================

source_hash = sha256_file(PDF)

source_stat = PDF.stat()

source_info = {
    "file_name": PDF.name,
    "absolute_path": str(PDF.resolve()),
    "size_bytes": source_stat.st_size,
    "sha256": source_hash,
    "modified_time": datetime.datetime.fromtimestamp(
        source_stat.st_mtime,
        tz=datetime.timezone.utc
    ).isoformat()
}

print("SOURCE INTEGRITY")
print(f"  SHA256 : {source_hash}")
print(f"  SIZE   : {source_stat.st_size:,} bytes")
print()

# ============================================================
# TESSERACT VERSION
# ============================================================

try:
    version_result = subprocess.run(
        [
            str(TESSERACT),
            "--version"
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30
    )

    tesseract_version = (
        version_result.stdout
        or version_result.stderr
    ).splitlines()[0].strip()

except Exception as exc:
    fail(
        f"Gagal membaca versi Tesseract: {exc}"
    )

print("OCR ENGINE")
print(f"  {tesseract_version}")
print("  LANGUAGE : ind")
print()

# ============================================================
# OPEN PDF
# ============================================================

try:
    document = fitz.open(PDF)
except Exception as exc:
    fail(
        f"PDF gagal dibuka:\n{exc}"
    )

page_count = len(document)

if page_count == 0:
    document.close()
    fail("PDF tidak memiliki halaman.")

print(f"PDF PAGES : {page_count}")
print()

# ============================================================
# RUN OCR
# ============================================================

all_pages = []
all_text = []

overall_word_count = 0
overall_confidence_values = []

processing_errors = []

for page_index in range(page_count):

    page_number = page_index + 1

    print(
        f"[{page_number}/{page_count}] "
        f"Processing page {page_number}"
    )

    try:

        page = document.load_page(page_index)

        # ----------------------------------------------------
        # Render 300 DPI equivalent
        # ----------------------------------------------------

        scale = 300 / 72

        matrix = fitz.Matrix(
            scale,
            scale
        )

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        image_path = (
            OUT
            / f"page_{page_number:03d}.png"
        )

        pix.save(str(image_path))

        # ----------------------------------------------------
        # Temporary OCR TSV
        # ----------------------------------------------------

        with tempfile.TemporaryDirectory() as tmp:

            tmp_dir = Path(tmp)

            input_image = tmp_dir / "page.png"

            shutil.copyfile(
                image_path,
                input_image
            )

            output_base = tmp_dir / "ocr"

            command = [
                str(TESSERACT),
                str(input_image),
                str(output_base),
                "-l",
                "ind",
                "--psm",
                "6",
                "tsv"
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180
            )

            if result.returncode != 0:
                raise RuntimeError(
                    "Tesseract exit code "
                    f"{result.returncode}: "
                    f"{result.stderr.strip()}"
                )

            tsv_file = Path(
                str(output_base) + ".tsv"
            )

            if not tsv_file.exists():
                raise RuntimeError(
                    "Output TSV Tesseract tidak ditemukan."
                )

            tsv = tsv_file.read_text(
                encoding="utf-8",
                errors="replace"
            )

        # ----------------------------------------------------
        # Parse TSV
        # ----------------------------------------------------

        lines = tsv.splitlines()

        if not lines:
            raise RuntimeError(
                "TSV OCR kosong."
            )

        words = []
        page_confidences = []

        header = lines[0].split("\t")

        required_columns = [
            "text",
            "conf",
            "left",
            "top",
            "width",
            "height",
            "block_num",
            "par_num",
            "line_num",
            "word_num"
        ]

        positions = {
            name: header.index(name)
            for name in required_columns
            if name in header
        }

        for line in lines[1:]:

            parts = line.split("\t")

            if len(parts) < len(header):
                continue

            text_value = safe_text(
                parts[positions["text"]]
            )

            if not text_value:
                continue

            try:
                confidence = float(
                    parts[positions["conf"]]
                )
            except Exception:
                confidence = -1

            try:
                left = int(
                    float(parts[positions["left"]])
                )
                top = int(
                    float(parts[positions["top"]])
                )
                width = int(
                    float(parts[positions["width"]])
                )
                height = int(
                    float(parts[positions["height"]])
                )
                block_num = int(
                    parts[positions["block_num"]]
                )
                par_num = int(
                    parts[positions["par_num"]]
                )
                line_num = int(
                    parts[positions["line_num"]]
                )
                word_num = int(
                    parts[positions["word_num"]]
                )
            except Exception:
                continue

            item = {
                "text": text_value,
                "confidence": round(
                    confidence,
                    2
                ),
                "left": left,
                "top": top,
                "width": width,
                "height": height,
                "right": left + width,
                "bottom": top + height,
                "block_num": block_num,
                "par_num": par_num,
                "line_num": line_num,
                "word_num": word_num
            }

            words.append(item)

            if confidence >= 0:
                page_confidences.append(
                    confidence
                )
                overall_confidence_values.append(
                    confidence
                )

        # ----------------------------------------------------
        # Reconstruct lines using Tesseract block/line
        # ----------------------------------------------------

        line_groups = {}

        for word in words:

            key = (
                word["block_num"],
                word["par_num"],
                word["line_num"]
            )

            line_groups.setdefault(
                key,
                []
            ).append(word)

        reconstructed_lines = []

        for key, line_words in line_groups.items():

            line_words = sorted(
                line_words,
                key=lambda x: x["left"]
            )

            text_value = " ".join(
                x["text"]
                for x in line_words
            )

            reconstructed_lines.append({
                "block_num": key[0],
                "par_num": key[1],
                "line_num": key[2],
                "top": min(
                    x["top"]
                    for x in line_words
                ),
                "bottom": max(
                    x["bottom"]
                    for x in line_words
                ),
                "left": min(
                    x["left"]
                    for x in line_words
                ),
                "right": max(
                    x["right"]
                    for x in line_words
                ),
                "text": text_value,
                "words": line_words
            })

        reconstructed_lines.sort(
            key=lambda x: (
                x["top"],
                x["left"]
            )
        )

        page_text = "\n".join(
            x["text"]
            for x in reconstructed_lines
        )

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        if page_confidences:

            average_confidence = (
                sum(page_confidences)
                / len(page_confidences)
            )

            low_confidence_count = sum(
                1
                for value in page_confidences
                if value < 60
            )

        else:

            average_confidence = 0
            low_confidence_count = 0

        page_result = {
            "page": page_number,
            "image": str(
                image_path.relative_to(ROOT)
            ),
            "width": pix.width,
            "height": pix.height,
            "word_count": len(words),
            "line_count": len(
                reconstructed_lines
            ),
            "average_confidence": round(
                average_confidence,
                2
            ),
            "low_confidence_words": (
                low_confidence_count
            ),
            "words": words,
            "lines": reconstructed_lines
        }

        all_pages.append(
            page_result
        )

        all_text.append(
            f"===== PAGE {page_number} =====\n"
            + page_text
        )

        overall_word_count += len(words)

        print(
            f"  WORDS : {len(words):,}"
        )

        print(
            f"  LINES : {len(reconstructed_lines):,}"
        )

        print(
            f"  CONF  : {average_confidence:.2f}"
        )

        print(
            f"  LOW<60: {low_confidence_count}"
        )

    except Exception as exc:

        processing_errors.append({
            "page": page_number,
            "error": str(exc)
        })

        print(
            f"  ERROR : {exc}"
        )

document.close()

# ============================================================
# GLOBAL CONFIDENCE
# ============================================================

if overall_confidence_values:

    global_confidence = (
        sum(overall_confidence_values)
        / len(overall_confidence_values)
    )

else:

    global_confidence = 0

# ============================================================
# TEXT ARTIFACT
# ============================================================

TEXT.write_text(
    "\n\n".join(all_text),
    encoding="utf-8"
)

# ============================================================
# LAYOUT ARTIFACT
# ============================================================

layout_result = {
    "schema_version": "2.0",
    "engine": {
        "name": "Nusantara Governance SOP OCR Engine",
        "version": VERSION,
        "generated_at": utc_now()
    },
    "source": source_info,
    "ocr": {
        "engine": tesseract_version,
        "language": "ind",
        "psm": 6,
        "resolution_dpi": 300,
        "coordinates": True,
        "confidence_recorded": True
    },
    "document": {
        "pages": page_count,
        "processed_pages": len(all_pages),
        "word_count": overall_word_count,
        "average_confidence": round(
            global_confidence,
            2
        )
    },
    "pages": all_pages
}

LAYOUT.write_text(
    json.dumps(
        layout_result,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

# ============================================================
# GOVERNANCE STATUS
# ============================================================

if processing_errors:

    status = "FAILED"

elif len(all_pages) != page_count:

    status = "FAILED"

elif overall_word_count == 0:

    status = "FAILED"

elif global_confidence < 50:

    status = "REVIEW_REQUIRED"

else:

    status = "READY_FOR_STRUCTURED_PARSING"

# IMPORTANT:
# Never mark verified automatically.

governance = {
    "schema_version": "2.0",

    "document_type": "SOP_TTE",

    "governance": {
        "status": status,
        "source_verification": "PENDING",
        "content_verification": "PENDING",
        "human_validation_required": True,
        "production_ingestion_allowed": False
    },

    "source": source_info,

    "processing": {
        "engine": "Nusantara Governance SOP OCR Engine",
        "version": VERSION,
        "timestamp_utc": utc_now(),
        "tesseract": tesseract_version,
        "language": "ind",
        "resolution_dpi": 300,
        "psm": 6
    },

    "quality": {
        "pdf_pages": page_count,
        "processed_pages": len(all_pages),
        "word_count": overall_word_count,
        "average_confidence": round(
            global_confidence,
            2
        ),
        "processing_errors": processing_errors
    },

    "artifacts": {
        "ocr_text": str(
            TEXT.relative_to(ROOT)
        ),
        "layout_json": str(
            LAYOUT.relative_to(ROOT)
        ),
        "report_json": str(
            REPORT.relative_to(ROOT)
        )
    },

    "security": {
        "original_pdf_modified": False,
        "production_database_modified": False,
        "automatic_verification": False
    }
}

REPORT.write_text(
    json.dumps(
        governance,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

# ============================================================
# ARTIFACT HASHES
# ============================================================

artifact_hashes = {}

for artifact in [
    TEXT,
    LAYOUT,
    REPORT
]:

    if artifact.exists():

        artifact_hashes[
            str(
                artifact.relative_to(ROOT)
            )
        ] = sha256_file(artifact)

governance["artifacts_sha256"] = artifact_hashes

REPORT.write_text(
    json.dumps(
        governance,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

# ============================================================
# FINAL
# ============================================================

print()
print("=" * 78)
print("GOVERNANCE OCR RESULT")
print("=" * 78)

print(
    f"STATUS             : {status}"
)

print(
    f"PDF PAGES          : {page_count}"
)

print(
    f"PROCESSED PAGES    : {len(all_pages)}"
)

print(
    f"OCR WORDS          : {overall_word_count:,}"
)

print(
    f"AVERAGE CONFIDENCE : {global_confidence:.2f}"
)

print()
print("SOURCE SHA256")
print(
    f"  {source_hash}"
)

print()
print("ARTIFACTS")

print(
    f"  TEXT   : {TEXT}"
)

print(
    f"  LAYOUT : {LAYOUT}"
)

print(
    f"  REPORT : {REPORT}"
)

print()
print("GOVERNANCE CONTROLS")

print("  Original PDF          : NOT MODIFIED")
print("  Production DB         : NOT TOUCHED")
print("  Automatic verification: DISABLED")
print("  Human validation      : REQUIRED")

if processing_errors:

    print()
    print("PROCESSING ERRORS:")

    for error in processing_errors:

        print(
            f"  PAGE {error['page']}: "
            f"{error['error']}"
        )

print("=" * 78)

if status == "FAILED":
    sys.exit(2)

if status == "REVIEW_REQUIRED":
    sys.exit(3)

sys.exit(0)
