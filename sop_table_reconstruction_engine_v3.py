from pathlib import Path
import json
import hashlib
import datetime
import re
import statistics

ROOT = Path.cwd()

BASE = ROOT / "data" / "knowledge" / "sop" / "extracted" / "CAPIL_02_GOVERNANCE_OCR"

LAYOUT = BASE / "layout.json"
VISION = BASE / "table_vision" / "table_vision.json"

OUT = BASE / "CAPIL-02_RECONSTRUCTED_V3"
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT / "sop_table_v3.json"
REPORT = OUT / "reconstruction_report_v3.json"


def now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def get_page_number(item, fallback):
    """
    Mendukung beberapa kemungkinan format table_vision.json.
    Tidak boleh menghasilkan None.
    """

    candidates = [
        item.get("page"),
        item.get("page_number"),
        item.get("page_no"),
        item.get("page_index"),
        item.get("number"),
    ]

    for value in candidates:
        if value is not None:
            try:
                return int(value)
            except Exception:
                pass

    filename = str(
        item.get("image")
        or item.get("file")
        or item.get("filename")
        or item.get("page_image")
        or ""
    )

    match = re.search(
        r"page[_\- ]?0*(\d+)",
        filename,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return fallback


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


def group_words_by_y(words, tolerance=20):

    rows = []

    for word in sorted(
        words,
        key=lambda w: (
            float(w.get("top", 0)),
            float(w.get("left", 0))
        )
    ):

        cy = word_center(word)[1]

        target = None

        for row in rows:
            if abs(cy - row["center_y"]) <= tolerance:
                target = row
                break

        if target is None:
            target = {
                "center_y": cy,
                "words": []
            }
            rows.append(target)

        target["words"].append(word)

        target["center_y"] = (
            sum(
                word_center(w)[1]
                for w in target["words"]
            )
            / len(target["words"])
        )

    for row in rows:
        row["words"].sort(
            key=lambda w: float(
                w.get("left", 0)
            )
        )

        row["text"] = clean(
            " ".join(
                w.get("text", "")
                for w in row["words"]
            )
        )

    return rows


def merge_positions(
    positions,
    tolerance=25
):

    values = []

    for value in positions or []:
        try:
            values.append(int(value))
        except Exception:
            continue

    values = sorted(set(values))

    if not values:
        return []

    groups = [[values[0]]]

    for value in values[1:]:

        if (
            value
            - statistics.mean(groups[-1])
            <= tolerance
        ):
            groups[-1].append(value)
        else:
            groups.append([value])

    return [
        int(round(statistics.mean(group)))
        for group in groups
    ]


def detect_header(words):

    terms = [
        "kegiatan",
        "pelaksana",
        "kelengkapan",
        "waktu",
        "output",
        "keterangan",
        "no"
    ]

    rows = group_words_by_y(
        words,
        tolerance=22
    )

    candidates = []

    for row in rows:

        text = row["text"].lower()

        found = [
            term
            for term in terms
            if re.search(
                r"\b" + re.escape(term) + r"\b",
                text
            )
        ]

        if len(set(found)) >= 2:
            candidates.append(
                (row, sorted(set(found)))
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            -len(item[1]),
            item[0]["center_y"]
        )
    )

    return candidates[0]


def normalize_page_words(page):

    """
    layout.json biasanya:
      page["words"]

    Tetapi beberapa versi bisa memakai:
      page["ocr_words"]
      page["items"]
    """

    words = (
        page.get("words")
        or page.get("ocr_words")
        or page.get("items")
        or []
    )

    normalized = []

    for word in words:

        if not isinstance(word, dict):
            continue

        text = clean(
            word.get("text")
        )

        if not text:
            continue

        normalized.append(word)

    return normalized


print("=" * 78)
print("NUSANTARA SOP TABLE RECONSTRUCTION ENGINE V3")
print("=" * 78)

print("VERSION : 3.1 FIXED")
print(f"LAYOUT  : {LAYOUT}")
print(f"VISION  : {VISION}")


if not LAYOUT.exists():
    raise SystemExit(
        "ERROR: layout.json tidak ditemukan."
    )

if not VISION.exists():
    raise SystemExit(
        "ERROR: table_vision.json tidak ditemukan."
    )


layout = json.loads(
    LAYOUT.read_text(
        encoding="utf-8"
    )
)

vision = json.loads(
    VISION.read_text(
        encoding="utf-8"
    )
)


# ============================================================
# NORMALIZE LAYOUT
# ============================================================

raw_layout_pages = (
    layout.get("pages")
    or layout.get("page_data")
    or []
)

layout_pages = {}

for index, page in enumerate(
    raw_layout_pages,
    start=1
):

    if not isinstance(page, dict):
        continue

    number = get_page_number(
        page,
        index
    )

    layout_pages[number] = page


# ============================================================
# NORMALIZE VISION
# ============================================================

if isinstance(
    vision,
    dict
):

    raw_vision_pages = (
        vision.get("pages")
        or vision.get("page_results")
        or vision.get("results")
        or []
    )

elif isinstance(
    vision,
    list
):

    raw_vision_pages = vision

else:

    raw_vision_pages = []


print()
print(
    f"LAYOUT PAGES DETECTED : "
    f"{len(layout_pages)}"
)

print(
    f"VISION PAGES DETECTED : "
    f"{len(raw_vision_pages)}"
)


if not raw_vision_pages:
    raise SystemExit(
        "ERROR: Tidak menemukan data halaman "
        "di table_vision.json."
    )


pages_result = []


for index, page_info in enumerate(
    raw_vision_pages,
    start=1
):

    if not isinstance(
        page_info,
        dict
    ):
        continue

    page_number = get_page_number(
        page_info,
        index
    )

    print()
    print(
        f"[PAGE {page_number}]"
    )

    if page_number not in layout_pages:

        print(
            "  WARNING: halaman tidak ditemukan "
            "di layout.json"
        )

        pages_result.append({
            "page": page_number,
            "status":
                "PAGE_NOT_FOUND_IN_LAYOUT"
        })

        continue


    source_page = layout_pages[
        page_number
    ]

    words = normalize_page_words(
        source_page
    )

    print(
        f"  OCR WORDS : {len(words)}"
    )


    # ========================================================
    # GET VISION GEOMETRY
    # ========================================================

    vertical_positions = (
        page_info.get(
            "vertical_positions"
        )
        or page_info.get(
            "vertical_lines"
        )
        or page_info.get(
            "v_positions"
        )
        or []
    )

    horizontal_positions = (
        page_info.get(
            "horizontal_positions"
        )
        or page_info.get(
            "horizontal_lines"
        )
        or page_info.get(
            "h_positions"
        )
        or []
    )


    vertical_positions = merge_positions(
        vertical_positions,
        tolerance=25
    )

    horizontal_positions = merge_positions(
        horizontal_positions,
        tolerance=18
    )


    if not vertical_positions:

        print(
            "  WARNING: vertical geometry kosong"
        )

    if not horizontal_positions:

        print(
            "  WARNING: horizontal geometry kosong"
        )


    # ========================================================
    # PAGE DIMENSION
    # ========================================================

    page_width = max(
        [
            float(
                w.get("right", 0)
            )
            for w in words
        ]
        or [0]
    )

    page_height = max(
        [
            float(
                w.get("bottom", 0)
            )
            for w in words
        ]
        or [0]
    )


    # ========================================================
    # HEADER
    # ========================================================

    header = detect_header(
        words
    )

    header_y = None

    if header:

        header_row, header_fields = header

        header_y = header_row[
            "center_y"
        ]

        print(
            "  HEADER : "
            + header_row["text"][:180]
        )

        print(
            "  FIELDS : "
            + ", ".join(header_fields)
        )

    else:

        print(
            "  HEADER : NOT DETECTED"
        )


    # ========================================================
    # COLUMN BOUNDARIES
    # ========================================================

    usable_vertical = [
        x
        for x in vertical_positions
        if x > 80
        and x < page_width - 80
    ]

    if len(
        usable_vertical
    ) < 3:

        usable_vertical = (
            vertical_positions
        )

    boundaries = (
        [0]
        + usable_vertical
        + [page_width]
    )

    boundaries = sorted(
        set(
            int(x)
            for x in boundaries
        )
    )


    columns = []

    for i in range(
        len(boundaries) - 1
    ):

        x0 = boundaries[i]
        x1 = boundaries[i + 1]

        if x1 - x0 < 60:
            continue

        columns.append({
            "column_index": i,
            "x0": x0,
            "x1": x1,
            "width": x1 - x0
        })


    print(
        f"  COLUMNS: {len(columns)}"
    )


    # ========================================================
    # TABLE VERTICAL RANGE
    # ========================================================

    if header_y is not None:

        lower_lines = [
            y
            for y in horizontal_positions
            if y > header_y + 20
        ]

        if lower_lines:
            table_bottom = max(
                lower_lines
            )
        else:
            table_bottom = page_height

        table_top = max(
            0,
            header_y - 100
        )

    else:

        table_top = 0
        table_bottom = page_height


    # ========================================================
    # ROW RECONSTRUCTION
    # ========================================================

    relevant_words = [
        word
        for word in words
        if (
            word_center(word)[1]
            >= table_top
            and
            word_center(word)[1]
            <= table_bottom
        )
    ]

    row_groups = group_words_by_y(
        relevant_words,
        tolerance=20
    )


    rows = []


    for row_group in row_groups:

        cy = row_group[
            "center_y"
        ]

        if (
            header_y is not None
            and cy <= header_y + 15
        ):
            continue


        cells = {}


        for column in columns:

            cell_words = []

            for word in row_group[
                "words"
            ]:

                cx = word_center(
                    word
                )[0]

                if (
                    cx >= column["x0"]
                    and
                    cx <= column["x1"]
                ):

                    cell_words.append(
                        word
                    )


            if not cell_words:
                continue


            cell_words.sort(
                key=lambda w:
                    float(
                        w.get(
                            "left",
                            0
                        )
                    )
            )


            text_value = clean(
                " ".join(
                    w.get(
                        "text",
                        ""
                    )
                    for w in cell_words
                )
            )


            if not text_value:
                continue


            confidences = []

            for word in cell_words:

                try:
                    confidences.append(
                        float(
                            word.get(
                                "confidence",
                                -1
                            )
                        )
                    )
                except Exception:
                    pass


            cells[
                str(
                    column[
                        "column_index"
                    ]
                )
            ] = {

                "text":
                    text_value,

                "word_count":
                    len(cell_words),

                "average_confidence":
                    round(
                        sum(confidences)
                        / len(confidences),
                        2
                    )
                    if confidences
                    else None,

                "minimum_confidence":
                    min(confidences)
                    if confidences
                    else None,

                "evidence_words":
                    [
                        {
                            "text":
                                w.get(
                                    "text"
                                ),
                            "left":
                                w.get(
                                    "left"
                                ),
                            "top":
                                w.get(
                                    "top"
                                ),
                            "right":
                                w.get(
                                    "right"
                                ),
                            "bottom":
                                w.get(
                                    "bottom"
                                ),
                            "confidence":
                                w.get(
                                    "confidence"
                                )
                        }
                        for w in cell_words
                    ]
            }


        if cells:

            rows.append({

                "y":
                    round(
                        cy,
                        2
                    ),

                "source_text":
                    row_group[
                        "text"
                    ],

                "cells":
                    cells
            })


    print(
        f"  ROWS   : {len(rows)}"
    )


    pages_result.append({

        "page":
            page_number,

        "status":
            "GEOMETRY_RECONSTRUCTED",

        "header":
            {
                "text":
                    header[0]["text"]
                    if header
                    else None,

                "fields":
                    header[1]
                    if header
                    else []
            },

        "geometry":
            {
                "page_width":
                    page_width,

                "page_height":
                    page_height,

                "vertical_boundaries":
                    boundaries,

                "horizontal_positions":
                    horizontal_positions,

                "table_top":
                    table_top,

                "table_bottom":
                    table_bottom
            },

        "columns":
            columns,

        "rows":
            rows
    })


# ============================================================
# GOVERNANCE RESULT
# ============================================================

result = {

    "schema_version":
        "3.1",

    "document_type":
        "SOP_TTE",

    "engine":
        {
            "name":
                "Nusantara SOP Table Reconstruction Engine",

            "version":
                "3.1",

            "mode":
                "coordinate_cell_reconstruction",

            "generated_at":
                now()
        },

    "source":
        {
            "layout":
                str(
                    LAYOUT.relative_to(
                        ROOT
                    )
                ),

            "layout_sha256":
                sha256(
                    LAYOUT
                ),

            "vision":
                str(
                    VISION.relative_to(
                        ROOT
                    )
                ),

            "vision_sha256":
                sha256(
                    VISION
                )
        },

    "pages":
        pages_result,

    "governance":
        {
            "status":
                "READY_FOR_HUMAN_VALIDATION",

            "source_verification":
                "PENDING",

            "content_verification":
                "PENDING",

            "automatic_verification":
                False,

            "production_ingestion":
                False,

            "production_db_modified":
                False,

            "original_pdf_modified":
                False,

            "ocr_evidence_modified":
                False,

            "human_validation_required":
                True
        }
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

    "engine":
        "Nusantara SOP Table Reconstruction Engine V3.1",

    "generated_at":
        now(),

    "layout_pages":
        len(layout_pages),

    "vision_pages":
        len(raw_vision_pages),

    "processed_pages":
        len(pages_result),

    "reconstructed_pages":
        sum(
            1
            for p in pages_result
            if p.get("status")
            == "GEOMETRY_RECONSTRUCTED"
        ),

    "total_rows":
        sum(
            len(
                p.get(
                    "rows",
                    []
                )
            )
            for p in pages_result
        ),

    "governance":
        result[
            "governance"
        ]
}


REPORT.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


print()
print("=" * 78)
print("RECONSTRUCTION V3.1 COMPLETE")
print("=" * 78)

print(
    f"PROCESSED PAGES : "
    f"{len(pages_result)}"
)

print(
    "RECONSTRUCTED   : "
    + str(
        sum(
            1
            for p in pages_result
            if p.get("status")
            == "GEOMETRY_RECONSTRUCTED"
        )
    )
)

print(
    "TOTAL ROWS      : "
    + str(
        sum(
            len(
                p.get(
                    "rows",
                    []
                )
            )
            for p in pages_result
        )
    )
)

print()
print("GOVERNANCE")
print("  Original PDF : NOT MODIFIED")
print("  OCR Evidence : NOT MODIFIED")
print("  Production DB: NOT TOUCHED")
print("  Verification : NOT AUTOMATIC")
print("  Human Review : REQUIRED")

print()
print(
    f"OUTPUT : {OUTPUT}"
)

print(
    f"REPORT : {REPORT}"
)

print("=" * 78)
