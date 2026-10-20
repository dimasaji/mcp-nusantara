from pathlib import Path
import json
import re
import hashlib
import subprocess
import shutil
import datetime
import statistics
import sys

# ============================================================
# NUSANTARA MASTER PDF SOP ENGINE
# VERSION 1.0
#
# GENERIC MULTI-SOP PDF -> OCR -> LAYOUT -> TABLE -> STRUCTURE
#
# GOVERNANCE:
#   Original PDF       : READ ONLY
#   Production DB      : NOT TOUCHED
#   Verification       : HUMAN REQUIRED
#   AI interpretation  : NOT USED FOR SOURCE CREATION
# ============================================================

ROOT = Path.cwd()

SOP_ROOT = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
)

ORIGINAL = SOP_ROOT / "original"

OUTPUT_ROOT = SOP_ROOT / "engine_output"

MANIFEST = SOP_ROOT / "engine_manifest.json"

TESSERACT = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

OCR_LANGUAGE = "ind"

DPI = 250

MIN_TEXT_LAYER_CHARS = 150

OCR_CONFIDENCE_REVIEW = 60.0

MAX_PREVIEW_ROWS = 100


# ============================================================
# UTILITIES
# ============================================================

def now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def sha256_file(path):

    h = hashlib.sha256()

    with open(
        path,
        "rb"
    ) as f:

        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b""
        ):
            h.update(chunk)

    return h.hexdigest()


def clean(text):

    return re.sub(
        r"\s+",
        " ",
        str(text or "")
    ).strip()


def safe_name(text):

    text = clean(text)

    text = re.sub(
        r"[<>:\"/\\|?*]",
        "_",
        text
    )

    text = re.sub(
        r"_+",
        "_",
        text
    )

    return text[:120] or "UNKNOWN_SOP"


def run_command(args):

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    return result


def write_json(path, data):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def word_center(word):

    return (
        (
            float(word.get("left", 0))
            + float(word.get("right", 0))
        ) / 2,

        (
            float(word.get("top", 0))
            + float(word.get("bottom", 0))
        ) / 2
    )


# ============================================================
# PDF IMPORT
# ============================================================

try:

    import pymupdf

except Exception:

    try:
        import fitz as pymupdf
    except Exception:
        pymupdf = None


try:

    import cv2
    import numpy as np

except Exception:

    cv2 = None
    np = None


# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_text_layer(pdf_path):

    if pymupdf is None:

        return {
            "available": False,
            "pages": [],
            "characters": 0
        }

    doc = pymupdf.open(
        str(pdf_path)
    )

    pages = []
    total = 0

    for page_number, page in enumerate(
        doc,
        start=1
    ):

        text = page.get_text(
            "text"
        )

        text = text or ""

        total += len(text)

        pages.append({

            "page":
                page_number,

            "text":
                text,

            "characters":
                len(text),

            "has_text":
                len(text.strip()) > 0
        })

    doc.close()

    return {

        "available":
            True,

        "pages":
            pages,

        "characters":
            total
    }


# ============================================================
# OCR
# ============================================================

def render_pdf_pages(
    pdf_path,
    image_dir
):

    image_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    doc = pymupdf.open(
        str(pdf_path)
    )

    images = []

    zoom = DPI / 72.0

    matrix = pymupdf.Matrix(
        zoom,
        zoom
    )

    for page_number, page in enumerate(
        doc,
        start=1
    ):

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        image_path = (
            image_dir
            / f"page_{page_number:03d}.png"
        )

        pix.save(
            str(image_path)
        )

        images.append({
            "page":
                page_number,

            "image":
                str(
                    image_path
                )
        })

    doc.close()

    return images


def tesseract_tsv(
    image_path
):

    result = run_command([
        str(TESSERACT),
        str(image_path),
        "stdout",
        "-l",
        OCR_LANGUAGE,
        "--psm",
        "6",
        "tsv"
    ])

    if result.returncode != 0:

        raise RuntimeError(
            result.stderr
            or
            "Tesseract gagal."
        )

    lines = result.stdout.splitlines()

    if not lines:
        return []

    header = lines[0].split("\t")

    words = []

    for line in lines[1:]:

        parts = line.split("\t")

        if len(parts) != len(header):
            continue

        row = dict(
            zip(
                header,
                parts
            )
        )

        text = clean(
            row.get(
                "text",
                ""
            )
        )

        if not text:
            continue

        try:

            conf = float(
                row.get(
                    "conf",
                    -1
                )
            )

            left = int(
                row.get(
                    "left",
                    0
                )
            )

            top = int(
                row.get(
                    "top",
                    0
                )
            )

            width = int(
                row.get(
                    "width",
                    0
                )
            )

            height = int(
                row.get(
                    "height",
                    0
                )
            )

        except Exception:

            continue

        words.append({

            "text":
                text,

            "confidence":
                conf,

            "left":
                left,

            "top":
                top,

            "width":
                width,

            "height":
                height,

            "right":
                left + width,

            "bottom":
                top + height,

            "block_num":
                row.get(
                    "block_num"
                ),

            "par_num":
                row.get(
                    "par_num"
                ),

            "line_num":
                row.get(
                    "line_num"
                ),

            "word_num":
                row.get(
                    "word_num"
                )
        })

    return words


# ============================================================
# OCR LINE RECONSTRUCTION
# ============================================================

def build_lines(words):

    groups = {}

    for word in words:

        key = (
            str(
                word.get(
                    "block_num"
                )
            ),
            str(
                word.get(
                    "par_num"
                )
            ),
            str(
                word.get(
                    "line_num"
                )
            )
        )

        groups.setdefault(
            key,
            []
        ).append(
            word
        )

    lines = []

    for key, group in groups.items():

        group.sort(
            key=lambda w:
                float(
                    w.get(
                        "left",
                        0
                    )
                )
        )

        text = clean(
            " ".join(
                w["text"]
                for w in group
            )
        )

        if not text:
            continue

        lines.append({

            "text":
                text,

            "words":
                len(group),

            "average_confidence":
                round(
                    sum(
                        float(
                            w.get(
                                "confidence",
                                -1
                            )
                        )
                        for w in group
                    )
                    / len(group),
                    2
                ),

            "left":
                min(
                    w["left"]
                    for w in group
                ),

            "top":
                min(
                    w["top"]
                    for w in group
                ),

            "right":
                max(
                    w["right"]
                    for w in group
                ),

            "bottom":
                max(
                    w["bottom"]
                    for w in group
                )
        })

    lines.sort(
        key=lambda x: (
            x["top"],
            x["left"]
        )
    )

    return lines


# ============================================================
# COMPUTER VISION TABLE DETECTION
# ============================================================

def detect_table_geometry(
    image_path
):

    if cv2 is None:

        return {
            "available":
                False,

            "reason":
                "OpenCV tidak tersedia"
        }

    image = cv2.imread(
        str(image_path),
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:

        return {
            "available":
                False,

            "reason":
                "Image tidak dapat dibaca"
        }

    height, width = image.shape

    # Binary inverse
    binary = cv2.threshold(
        image,
        200,
        255,
        cv2.THRESH_BINARY_INV
    )[1]

    # --------------------------------------------------------
    # Horizontal structures
    # --------------------------------------------------------

    horizontal_kernel_size = max(
        30,
        width // 25
    )

    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            horizontal_kernel_size,
            1
        )
    )

    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        horizontal_kernel
    )

    # --------------------------------------------------------
    # Vertical structures
    # --------------------------------------------------------

    vertical_kernel_size = max(
        30,
        height // 25
    )

    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            1,
            vertical_kernel_size
        )
    )

    vertical = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        vertical_kernel
    )

    horizontal_lines = []

    contours, _ = cv2.findContours(
        horizontal,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if (
            w >= width * 0.20
            and
            w >= h * 10
        ):

            horizontal_lines.append({

                "x1": x,
                "y1": y,
                "x2": x + w,
                "y2": y,

                "length":
                    w
            })

    vertical_lines = []

    contours, _ = cv2.findContours(
        vertical,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if (
            h >= height * 0.15
            and
            h >= w * 10
        ):

            vertical_lines.append({

                "x1": x,
                "y1": y,
                "x2": x,
                "y2": y + h,

                "length":
                    h
            })

    horizontal_lines.sort(
        key=lambda x:
            x["length"],
        reverse=True
    )

    vertical_lines.sort(
        key=lambda x:
            x["length"],
        reverse=True
    )

    # --------------------------------------------------------
    # Cluster X / Y positions
    # --------------------------------------------------------

    def cluster(values, tolerance=20):

        values = sorted(
            set(
                int(v)
                for v in values
            )
        )

        if not values:
            return []

        groups = [
            [values[0]]
        ]

        for value in values[1:]:

            if (
                value
                - statistics.mean(
                    groups[-1]
                )
                <= tolerance
            ):

                groups[-1].append(
                    value
                )

            else:

                groups.append(
                    [value]
                )

        return [
            int(
                round(
                    statistics.mean(
                        group
                    )
                )
            )
            for group in groups
        ]


    x_positions = cluster(
        [
            line["x1"]
            for line in vertical_lines
        ]
        +
        [
            line["x2"]
            for line in vertical_lines
        ]
    )

    y_positions = cluster(
        [
            line["y1"]
            for line in horizontal_lines
        ]
        +
        [
            line["y2"]
            for line in horizontal_lines
        ]
    )

    # --------------------------------------------------------
    # Candidate table regions
    # --------------------------------------------------------

    regions = []

    for y0 in y_positions:

        for y1 in y_positions:

            if y1 <= y0:
                continue

            if (
                y1 - y0
                < height * 0.15
            ):
                continue

            x0_candidates = [
                x
                for x in x_positions
                if x < width * 0.25
            ]

            x1_candidates = [
                x
                for x in x_positions
                if x > width * 0.60
            ]

            if not x0_candidates:
                continue

            if not x1_candidates:
                continue

            x0 = min(
                x0_candidates
            )

            x1 = max(
                x1_candidates
            )

            if (
                x1 - x0
                < width * 0.40
            ):
                continue

            area = (
                x1 - x0
            ) * (
                y1 - y0
            )

            regions.append({

                "x0":
                    x0,

                "y0":
                    y0,

                "x1":
                    x1,

                "y1":
                    y1,

                "area":
                    area
            })


    regions.sort(
        key=lambda x:
            x["area"],
        reverse=True
    )

    best_region = (
        regions[0]
        if regions
        else None
    )

    return {

        "available":
            True,

        "image_width":
            width,

        "image_height":
            height,

        "horizontal_lines":
            horizontal_lines[:100],

        "vertical_lines":
            vertical_lines[:100],

        "x_positions":
            x_positions,

        "y_positions":
            y_positions,

        "candidate_regions":
            regions[:20],

        "best_region":
            best_region
    }


# ============================================================
# OCR ROWS
# ============================================================

def group_rows(
    words,
    tolerance=20
):

    rows = []

    for word in sorted(
        words,
        key=lambda w: (
            float(w["top"]),
            float(w["left"])
        )
    ):

        cy = (
            float(word["top"])
            +
            float(word["bottom"])
        ) / 2

        selected = None

        for row in rows:

            if (
                abs(
                    cy
                    - row["center_y"]
                )
                <= tolerance
            ):

                selected = row
                break

        if selected is None:

            selected = {

                "center_y":
                    cy,

                "words":
                    []
            }

            rows.append(
                selected
            )

        selected["words"].append(
            word
        )

        selected["center_y"] = (
            sum(
                (
                    float(w["top"])
                    +
                    float(w["bottom"])
                ) / 2
                for w in selected["words"]
            )
            / len(
                selected["words"]
            )
        )


    result = []

    for row in rows:

        row["words"].sort(
            key=lambda w:
                float(
                    w["left"]
                )
        )

        text = clean(
            " ".join(
                w["text"]
                for w in row["words"]
            )
        )

        result.append({

            "y":
                round(
                    row["center_y"],
                    2
                ),

            "text":
                text,

            "words":
                row["words"]
        })

    return result


# ============================================================
# TABLE CELL RECONSTRUCTION
# ============================================================

def reconstruct_table(
    words,
    geometry
):

    region = geometry.get(
        "best_region"
    )

    if not region:

        return {
            "status":
                "NO_TABLE_GEOMETRY",

            "columns":
                [],

            "rows":
                []
        }


    x_positions = geometry.get(
        "x_positions",
        []
    )

    y_positions = geometry.get(
        "y_positions",
        []
    )


    if len(x_positions) < 2:

        return {
            "status":
                "INSUFFICIENT_COLUMN_GEOMETRY",

            "columns":
                [],

            "rows":
                []
        }


    x_positions = [
        x
        for x in x_positions
        if (
            x >= region["x0"]
            and
            x <= region["x1"]
        )
    ]


    if len(x_positions) < 2:

        return {
            "status":
                "INSUFFICIENT_COLUMN_GEOMETRY",

            "columns":
                [],

            "rows":
                []
        }


    x_positions = sorted(
        set(x_positions)
    )


    columns = []

    for i in range(
        len(x_positions) - 1
    ):

        x0 = x_positions[i]
        x1 = x_positions[i + 1]

        if (
            x1 - x0
            < 50
        ):
            continue

        columns.append({

            "index":
                len(columns),

            "x0":
                x0,

            "x1":
                x1,

            "width":
                x1 - x0
        })


    relevant_words = [

        word

        for word in words

        if (

            word_center(word)[0]
            >= region["x0"]

            and

            word_center(word)[0]
            <= region["x1"]

            and

            word_center(word)[1]
            >= region["y0"]

            and

            word_center(word)[1]
            <= region["y1"]
        )
    ]


    rows = group_rows(
        relevant_words
    )


    structured_rows = []


    for row in rows:

        cells = []


        for column in columns:

            cell_words = [

                word

                for word in row["words"]

                if (

                    word_center(word)[0]
                    >= column["x0"]

                    and

                    word_center(word)[0]
                    <= column["x1"]
                )
            ]


            if not cell_words:
                cells.append({
                    "text":
                        "",
                    "confidence":
                        None,
                    "evidence":
                        []
                })
                continue


            cell_words.sort(
                key=lambda w:
                    float(
                        w["left"]
                    )
            )


            text = clean(
                " ".join(
                    w["text"]
                    for w in cell_words
                )
            )


            confidence = round(
                sum(
                    float(
                        w.get(
                            "confidence",
                            -1
                        )
                    )
                    for w in cell_words
                )
                / len(
                    cell_words
                ),
                2
            )


            cells.append({

                "text":
                    text,

                "confidence":
                    confidence,

                "evidence":
                    [
                        {
                            "text":
                                w["text"],

                            "bbox":
                                [
                                    w["left"],
                                    w["top"],
                                    w["right"],
                                    w["bottom"]
                                ],

                            "confidence":
                                w["confidence"]
                        }

                        for w in cell_words
                    ]
            })


        if any(
            cell["text"]
            for cell in cells
        ):

            structured_rows.append({

                "y":
                    row["y"],

                "cells":
                    cells
            })


    return {

        "status":
            "TABLE_RECONSTRUCTED",

        "region":
            region,

        "columns":
            columns,

        "rows":
            structured_rows
    }


# ============================================================
# SOP METADATA EXTRACTION
# ============================================================

def first_match(
    text,
    patterns
):

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return clean(
                match.group(1)
            )

    return None


def extract_identity(
    all_text
):

    sop_number = first_match(
        all_text,
        [
            r"\bNO\s*SOP\s*[:\-]\s*([A-Z0-9./_-]+)",
            r"\bSOP\s*NO\s*[:\-]\s*([A-Z0-9./_-]+)"
        ]
    )


    effective_date = first_match(
        all_text,
        [
            r"TGL\s+TERBIT\s*[:\-]\s*([^\n]+)",
            r"TANGGAL\s+TERBIT\s*[:\-]\s*([^\n]+)"
        ]
    )


    title = first_match(
        all_text,
        [
            r"NAMA\s+SOP\s*[:\-]\s*([^\n]+)",
            r"JUDUL\s+SOP\s*[:\-]\s*([^\n]+)"
        ]
    )


    return {

        "sop_number":
            sop_number,

        "effective_date":
            effective_date,

        "title":
            title
    }


# ============================================================
# SEMANTIC CANDIDATE EXTRACTION
# ============================================================

def extract_requirements(
    lines
):

    candidates = []

    keywords = [
        "persyaratan",
        "kelengkapan",
        "fc ",
        "fotokopi",
        "fotocopy",
        "ktp",
        "kartu keluarga",
        "akta",
        "surat",
        "dokumen"
    ]

    for line in lines:

        text = clean(
            line["text"]
        )

        lower = text.lower()

        if any(
            key in lower
            for key in keywords
        ):

            if len(text) <= 250:

                candidates.append({

                    "text":
                        text,

                    "page":
                        line.get(
                            "page"
                        ),

                    "bbox":
                        [
                            line.get(
                                "left"
                            ),
                            line.get(
                                "top"
                            ),
                            line.get(
                                "right"
                            ),
                            line.get(
                                "bottom"
                            )
                        ],

                    "confidence":
                        line.get(
                            "average_confidence"
                        )
                })


    return candidates[:100]


def extract_times(
    text
):

    patterns = [

        r"\b\d+\s*(?:menit|jam|hari kerja|hari)\b",

        r"\b\d+\s*-\s*\d+\s*(?:menit|jam|hari kerja)\b"

    ]

    found = []

    for pattern in patterns:

        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE
        ):

            value = clean(
                match.group(0)
            )

            if value not in found:
                found.append(value)

    return found


def extract_outputs(
    text
):

    keywords = [
        "akta kelahiran",
        "akta kematian",
        "kartu keluarga",
        "kia",
        "ktp-el",
        "surat keterangan",
        "dokumen"
    ]

    result = []

    lower = text.lower()

    for keyword in keywords:

        if keyword in lower:

            result.append(
                keyword
            )

    return result


def extract_legal_basis(
    text
):

    patterns = [

        r"Undang-Undang[^\n|]+",

        r"Peraturan Pemerintah[^\n|]+",

        r"Peraturan Presiden[^\n|]+",

        r"Peraturan Menteri[^\n|]+",

        r"Peraturan Daerah[^\n|]+",

        r"Peraturan Walikota[^\n|]+"
    ]

    results = []

    for pattern in patterns:

        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE
        ):

            value = clean(
                match.group(0)
            )

            if (
                value
                and
                value not in results
            ):

                results.append(
                    value
                )

    return results[:100]


# ============================================================
# QUALITY GATE
# ============================================================

def quality_gate(
    document
):

    warnings = []

    errors = []


    source = document.get(
        "source",
        {}
    )

    pages = document.get(
        "pages",
        []
    )


    if not source.get(
        "sha256"
    ):

        errors.append(
            "SOURCE_HASH_MISSING"
        )


    if not pages:

        errors.append(
            "NO_PAGES"
        )


    average_confidences = [

        page.get(
            "average_confidence"
        )

        for page in pages

        if page.get(
            "average_confidence"
        ) is not None
    ]


    overall_confidence = (

        sum(
            average_confidences
        )
        /
        len(
            average_confidences
        )

        if average_confidences

        else 0
    )


    if (
        overall_confidence
        < OCR_CONFIDENCE_REVIEW
    ):

        warnings.append(
            "LOW_OCR_CONFIDENCE"
        )


    tables = [

        page.get(
            "table",
            {}
        )

        for page in pages
    ]


    reconstructed = sum(

        1

        for table in tables

        if table.get(
            "status"
        )
        ==
        "TABLE_RECONSTRUCTED"
    )


    if (
        reconstructed
        == 0
    ):

        warnings.append(
            "NO_TABLE_RECONSTRUCTED"
        )


    identity = document.get(
        "identity",
        {}
    )


    if not identity.get(
        "title"
    ):

        warnings.append(
            "TITLE_NOT_DETECTED"
        )


    if not identity.get(
        "sop_number"
    ):

        warnings.append(
            "SOP_NUMBER_NOT_DETECTED"
        )


    # --------------------------------------------------------
    # Important:
    # never auto-verify
    # --------------------------------------------------------

    if errors:

        status = "REJECTED"

    elif warnings:

        status = "REVIEW_REQUIRED"

    else:

        status = "READY_FOR_HUMAN_VALIDATION"


    return {

        "status":
            status,

        "errors":
            errors,

        "warnings":
            warnings,

        "overall_ocr_confidence":
            round(
                overall_confidence,
                2
            ),

        "reconstructed_tables":
            reconstructed,

        "automatic_verification":
            False,

        "human_validation_required":
            True,

        "production_ingestion_allowed":
            False
    }


# ============================================================
# PROCESS ONE PDF
# ============================================================

def process_pdf(
    pdf_path
):

    print()
    print("=" * 78)
    print(
        f"PROCESSING : {pdf_path.name}"
    )
    print("=" * 78)


    file_hash = sha256_file(
        pdf_path
    )

    file_size = pdf_path.stat().st_size


    text_dir = (
        OUTPUT_ROOT
        / safe_name(
            pdf_path.stem
        )
        / "text"
    )

    ocr_dir = (
        OUTPUT_ROOT
        / safe_name(
            pdf_path.stem
        )
        / "ocr"
    )

    layout_dir = (
        OUTPUT_ROOT
        / safe_name(
            pdf_path.stem
        )
        / "layout"
    )

    table_dir = (
        OUTPUT_ROOT
        / safe_name(
            pdf_path.stem
        )
        / "tables"
    )

    structured_dir = (
        OUTPUT_ROOT
        / safe_name(
            pdf_path.stem
        )
        / "structured"
    )

    quality_dir = (
        OUTPUT_ROOT
        / safe_name(
            pdf_path.stem
        )
        / "quality"
    )


    for directory in [
        text_dir,
        ocr_dir,
        layout_dir,
        table_dir,
        structured_dir,
        quality_dir
    ]:

        directory.mkdir(
            parents=True,
            exist_ok=True
        )


    # --------------------------------------------------------
    # TEXT LAYER
    # --------------------------------------------------------

    text_result = extract_text_layer(
        pdf_path
    )

    text_available = (
        text_result["characters"]
        >= MIN_TEXT_LAYER_CHARS
    )


    print(
        f"FILE SIZE       : "
        f"{file_size:,} bytes"
    )

    print(
        f"SHA256          : "
        f"{file_hash}"
    )

    print(
        f"TEXT LAYER CHARS: "
        f"{text_result['characters']}"
    )

    print(
        "MODE            : "
        + (
            "TEXT + OCR LAYOUT"
            if text_available
            else "OCR"
        )
    )


    # Save raw text layer
    write_json(
        text_dir / "text_layer.json",
        text_result
    )


    all_pages = []


    # --------------------------------------------------------
    # RENDER + OCR
    # --------------------------------------------------------

    if pymupdf is None:

        raise RuntimeError(
            "PyMuPDF tidak tersedia."
        )


    images = render_pdf_pages(
        pdf_path,
        ocr_dir / "pages"
    )


    for image_info in images:

        page_number = image_info[
            "page"
        ]

        image_path = Path(
            image_info[
                "image"
            ]
        )


        print(
            f"  PAGE {page_number}: "
            f"OCR"
        )


        words = tesseract_tsv(
            image_path
        )


        lines = build_lines(
            words
        )


        average_confidence = (

            sum(
                float(
                    w.get(
                        "confidence",
                        -1
                    )
                )
                for w in words
                if float(
                    w.get(
                        "confidence",
                        -1
                    )
                ) >= 0
            )
            /
            max(
                1,
                sum(
                    1
                    for w in words
                    if float(
                        w.get(
                            "confidence",
                            -1
                        )
                    ) >= 0
                )
            )
        )


        for line in lines:

            line["page"] = (
                page_number
            )


        for word in words:

            word["page"] = (
                page_number
            )


        page_text = clean(
            " ".join(
                w["text"]
                for w in words
            )
        )


        geometry = detect_table_geometry(
            image_path
        )


        table = reconstruct_table(
            words,
            geometry
        )


        page_result = {

            "page":
                page_number,

            "image":
                str(
                    image_path
                ),

            "word_count":
                len(words),

            "line_count":
                len(lines),

            "average_confidence":
                round(
                    average_confidence,
                    2
                ),

            "text":
                page_text,

            "words":
                words,

            "lines":
                lines,

            "geometry":
                geometry,

            "table":
                table
        }


        all_pages.append(
            page_result
        )


        write_json(
            layout_dir
            / f"page_{page_number:03d}.json",
            page_result
        )


        write_json(
            table_dir
            / f"page_{page_number:03d}_table.json",
            table
        )


    # --------------------------------------------------------
    # DOCUMENT TEXT
    # --------------------------------------------------------

    all_text = "\n".join(
        page["text"]
        for page in all_pages
    )


    identity = extract_identity(
        all_text
    )


    requirements = extract_requirements(

        [
            line

            for page in all_pages

            for line in page["lines"]
        ]
    )


    times = extract_times(
        all_text
    )


    outputs = extract_outputs(
        all_text
    )


    legal_basis = extract_legal_basis(
        all_text
    )


    # --------------------------------------------------------
    # TABLE SUMMARY
    # --------------------------------------------------------

    table_summary = []

    for page in all_pages:

        table = page[
            "table"
        ]

        table_summary.append({

            "page":
                page["page"],

            "status":
                table.get(
                    "status"
                ),

            "columns":
                len(
                    table.get(
                        "columns",
                        []
                    )
                ),

            "rows":
                len(
                    table.get(
                        "rows",
                        []
                    )
                ),

            "region":
                table.get(
                    "region"
                )
        })


    # --------------------------------------------------------
    # STRUCTURED SOP
    # --------------------------------------------------------

    document = {

        "schema_version":
            "1.0",

        "document_type":
            "SOP_TTE",

        "identity":
            identity,

        "source":
            {

                "source_file":
                    pdf_path.name,

                "source_path":
                    str(
                        pdf_path
                    ),

                "sha256":
                    file_hash,

                "file_size":
                    file_size,

                "source_status":
                    "official",

                "authority":
                    "official",

                "verification_status":
                    "pending_validation",

                "ocr_engine":
                    "Tesseract",

                "ocr_language":
                    OCR_LANGUAGE,

                "ocr_dpi":
                    DPI
            },

        "classification":
            {

                "service":
                    None,

                "scenario":
                    None,

                "intent":
                    None
            },

        "requirements":
            requirements,

        "procedure":
            [],

        "processing_time":
            times,

        "outputs":
            outputs,

        "legal_basis":
            legal_basis,

        "pages":
            all_pages,

        "table_summary":
            table_summary,

        "governance":
            {

                "original_pdf_modified":
                    False,

                "ocr_evidence_modified":
                    False,

                "production_db_modified":
                    False,

                "automatic_verification":
                    False,

                "human_validation_required":
                    True
            }
    }


    # --------------------------------------------------------
    # QUALITY
    # --------------------------------------------------------

    quality = quality_gate(
        document
    )


    document[
        "quality_gate"
    ] = quality


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    structured_path = (
        structured_dir
        / "sop_structured.json"
    )

    quality_path = (
        quality_dir
        / "quality_gate.json"
    )


    write_json(
        structured_path,
        document
    )


    write_json(
        quality_path,
        quality
    )


    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    result = {

        "source_file":
            pdf_path.name,

        "sha256":
            file_hash,

        "status":
            quality["status"],

        "pages":
            len(
                all_pages
            ),

        "ocr_words":
            sum(
                page["word_count"]
                for page in all_pages
            ),

        "average_ocr_confidence":
            quality[
                "overall_ocr_confidence"
            ],

        "tables":
            sum(
                1
                for x in table_summary
                if x["status"]
                ==
                "TABLE_RECONSTRUCTED"
            ),

        "requirements":
            len(
                requirements
            ),

        "processing_times":
            times,

        "outputs":
            outputs,

        "legal_basis":
            len(
                legal_basis
            ),

        "structured_output":
            str(
                structured_path
            ),

        "quality_output":
            str(
                quality_path
            )
    }


    write_json(
        structured_dir
        / "processing_report.json",
        result
    )


    print()
    print(
        "RESULT"
    )

    print(
        f"  STATUS       : "
        f"{quality['status']}"
    )

    print(
        f"  PAGES        : "
        f"{len(all_pages)}"
    )

    print(
        f"  OCR WORDS    : "
        f"{result['ocr_words']}"
    )

    print(
        f"  OCR CONF     : "
        f"{result['average_ocr_confidence']:.2f}"
    )

    print(
        f"  TABLES       : "
        f"{result['tables']}"
    )

    print(
        f"  REQUIREMENTS : "
        f"{result['requirements']}"
    )

    print(
        f"  TIME         : "
        f"{', '.join(times)}"
    )

    print(
        f"  OUTPUT       : "
        f"{', '.join(outputs)}"
    )

    print(
        f"  LEGAL BASIS  : "
        f"{len(legal_basis)}"
    )

    if quality["warnings"]:

        print(
            "  WARNINGS:"
        )

        for warning in quality[
            "warnings"
        ]:

            print(
                f"    - {warning}"
            )


    print(
        f"  JSON         : "
        f"{structured_path}"
    )

    return result


# ============================================================
# MAIN BATCH ENGINE
# ============================================================

def main():

    print()
    print("=" * 78)
    print("NUSANTARA MASTER PDF SOP ENGINE")
    print("VERSION 1.0")
    print("=" * 78)

    print(
        f"ROOT       : {ROOT}"
    )

    print(
        f"INPUT      : {ORIGINAL}"
    )

    print(
        f"OUTPUT     : {OUTPUT_ROOT}"
    )

    print(
        f"TESSERACT  : {TESSERACT}"
    )

    print(
        f"OCR LANG   : {OCR_LANGUAGE}"
    )

    print(
        f"DPI        : {DPI}"
    )

    print()


    if not ORIGINAL.exists():

        raise SystemExit(
            f"Folder tidak ditemukan: "
            f"{ORIGINAL}"
        )


    if not TESSERACT.exists():

        raise SystemExit(
            "Tesseract tidak ditemukan: "
            f"{TESSERACT}"
        )


    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )


    pdfs = sorted(
        ORIGINAL.glob(
            "*.pdf"
        )
    )


    if not pdfs:

        raise SystemExit(
            "Tidak ada PDF di folder original."
        )


    print(
        f"PDF DITEMUKAN : "
        f"{len(pdfs)}"
    )


    manifest = {

        "engine":
            {
                "name":
                    "Nusantara Master PDF SOP Engine",

                "version":
                    "1.0",

                "generated_at":
                    now()
            },

        "input":
            str(
                ORIGINAL
            ),

        "output":
            str(
                OUTPUT_ROOT
            ),

        "governance":
            {
                "original_pdf_modified":
                    False,

                "production_db_modified":
                    False,

                "automatic_verification":
                    False,

                "human_validation_required":
                    True,

                "production_ingestion":
                    False
            },

        "documents":
            []
    }


    for index, pdf in enumerate(
        pdfs,
        start=1
    ):

        print()
        print(
            f"[{index}/{len(pdfs)}] "
            f"{pdf.name}"
        )

        try:

            result = process_pdf(
                pdf
            )

            manifest[
                "documents"
            ].append(
                result
            )

        except Exception as exc:

            print(
                "  ERROR : "
                + str(exc)
            )

            manifest[
                "documents"
            ].append({

                "source_file":
                    pdf.name,

                "status":
                    "ENGINE_ERROR",

                "error":
                    str(exc)
            })


    manifest[
        "summary"
    ] = {

        "total_pdf":
            len(pdfs),

        "processed":
            sum(
                1
                for x
                in manifest[
                    "documents"
                ]
                if x.get(
                    "status"
                )
                not in [
                    "ENGINE_ERROR"
                ]
            ),

        "engine_error":
            sum(
                1
                for x
                in manifest[
                    "documents"
                ]
                if x.get(
                    "status"
                )
                ==
                "ENGINE_ERROR"
            ),

        "ready_for_human_validation":
            sum(
                1
                for x
                in manifest[
                    "documents"
                ]
                if x.get(
                    "status"
                )
                ==
                "READY_FOR_HUMAN_VALIDATION"
            ),

        "review_required":
            sum(
                1
                for x
                in manifest[
                    "documents"
                ]
                if x.get(
                    "status"
                )
                ==
                "REVIEW_REQUIRED"
            ),

        "rejected":
            sum(
                1
                for x
                in manifest[
                    "documents"
                ]
                if x.get(
                    "status"
                )
                ==
                "REJECTED"
            )
    }


    write_json(
        MANIFEST,
        manifest
    )


    print()
    print("=" * 78)
    print("MASTER SOP ENGINE COMPLETE")
    print("=" * 78)

    print(
        f"TOTAL PDF       : "
        f"{manifest['summary']['total_pdf']}"
    )

    print(
        f"PROCESSED       : "
        f"{manifest['summary']['processed']}"
    )

    print(
        f"ENGINE ERROR    : "
        f"{manifest['summary']['engine_error']}"
    )

    print(
        f"READY VALIDATION: "
        f"{manifest['summary']['ready_for_human_validation']}"
    )

    print(
        f"REVIEW REQUIRED : "
        f"{manifest['summary']['review_required']}"
    )

    print(
        f"REJECTED        : "
        f"{manifest['summary']['rejected']}"
    )

    print()
    print(
        f"MANIFEST : {MANIFEST}"
    )

    print()
    print("GOVERNANCE")
    print(
        "  Original PDF       : NOT MODIFIED"
    )
    print(
        "  Production DB      : NOT TOUCHED"
    )
    print(
        "  Automatic verify   : DISABLED"
    )
    print(
        "  Human validation   : REQUIRED"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()
