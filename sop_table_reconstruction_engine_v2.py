from pathlib import Path
import json
import hashlib
import datetime
import re
import statistics
import sys

# ============================================================
# NUSANTARA SOP TABLE RECONSTRUCTION ENGINE V2
# GOVERNANCE-GRADE
#
# IMPORTANT:
# This engine interprets OCR coordinates but NEVER changes
# the original PDF or OCR evidence.
#
# Production Knowledge DB is NEVER touched.
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

OUT = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
    / "parsed"
    / "CAPIL-02_RECONSTRUCTED_V2"
)

OUTPUT = OUT / "sop_table_v2.json"
REPORT = OUT / "reconstruction_report_v2.json"

ENGINE = "Nusantara SOP Table Reconstruction Engine"
VERSION = "2.0"


# ============================================================
# HELPERS
# ============================================================

def now_utc():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def sha256_file(path):

    h = hashlib.sha256()

    with path.open("rb") as f:

        while True:

            chunk = f.read(
                1024 * 1024
            )

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


def normalize(value):

    return clean(value).lower()


def fail(message):

    print()
    print("=" * 78)
    print("TABLE RECONSTRUCTION V2 : FAIL-CLOSED")
    print("=" * 78)
    print(message)
    print("=" * 78)

    sys.exit(2)


# ============================================================
# LOAD
# ============================================================

print("=" * 78)
print("NUSANTARA SOP TABLE RECONSTRUCTION ENGINE V2")
print("=" * 78)

print(
    f"VERSION : {VERSION}"
)

print(
    f"INPUT   : {INPUT}"
)

if not INPUT.exists():

    fail(
        f"layout.json tidak ditemukan:\n{INPUT}"
    )

try:

    data = json.loads(
        INPUT.read_text(
            encoding="utf-8"
        )
    )

except Exception as exc:

    fail(
        f"layout.json invalid:\n{exc}"
    )

layout_hash = sha256_file(
    INPUT
)

OUT.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# TABLE HEADER DICTIONARY
# ============================================================

HEADER_ALIASES = {

    "no": [
        "no",
        "nomor"
    ],

    "activity": [
        "kegiatan",
        "aktivitas",
        "kegiatan / aktivitas",
        "kegiatan/aktivitas"
    ],

    "actor": [
        "pelaksana",
        "pelaksana kegiatan",
        "petugas"
    ],

    "requirement": [
        "kelengkapan",
        "persyaratan",
        "dokumen",
        "kelengkapan/persyaratan"
    ],

    "time": [
        "waktu",
        "durasi"
    ],

    "output": [
        "output",
        "hasil"
    ],

    "quality": [
        "mutu baku"
    ],

    "note": [
        "keterangan"
    ]
}


# ============================================================
# PAGE ROW GROUPING
# ============================================================

def build_rows(page):

    words = page.get(
        "words",
        []
    )

    if not words:
        return []

    # Tesseract line number is more reliable than
    # manually grouping every word.
    groups = {}

    for word in words:

        key = (
            word.get("block_num", 0),
            word.get("par_num", 0),
            word.get("line_num", 0)
        )

        groups.setdefault(
            key,
            []
        ).append(word)

    rows = []

    for key, row_words in groups.items():

        row_words.sort(
            key=lambda x: x.get(
                "left",
                0
            )
        )

        text = clean(
            " ".join(
                w.get(
                    "text",
                    ""
                )
                for w in row_words
            )
        )

        if not text:
            continue

        rows.append({

            "block": key[0],
            "paragraph": key[1],
            "line": key[2],

            "top": min(
                w.get(
                    "top",
                    0
                )
                for w in row_words
            ),

            "bottom": max(
                w.get(
                    "bottom",
                    0
                )
                for w in row_words
            ),

            "left": min(
                w.get(
                    "left",
                    0
                )
                for w in row_words
            ),

            "right": max(
                w.get(
                    "right",
                    0
                )
                for w in row_words
            ),

            "text": text,

            "words": row_words
        })

    rows.sort(
        key=lambda x: (
            x["top"],
            x["left"]
        )
    )

    return rows


# ============================================================
# HEADER MATCHING
# ============================================================

def header_type(text):

    normalized = normalize(
        text
    )

    # Exact / near exact matching.
    for field, aliases in HEADER_ALIASES.items():

        for alias in aliases:

            alias_normalized = normalize(
                alias
            )

            if normalized == alias_normalized:
                return field, 1.0

    # Partial matching.
    for field, aliases in HEADER_ALIASES.items():

        for alias in aliases:

            alias_normalized = normalize(
                alias
            )

            if (
                len(alias_normalized) >= 4
                and alias_normalized in normalized
            ):
                return field, 0.75

    return None, 0.0


# ============================================================
# FIND TABLE HEADER
# ============================================================

def detect_table_header(rows):

    candidates = []

    for row_index, row in enumerate(rows):

        matched = []

        for word in row["words"]:

            field, score = header_type(
                word.get(
                    "text",
                    ""
                )
            )

            if field:

                matched.append({
                    "field": field,
                    "score": score,
                    "word": word
                })

        fields = {
            x["field"]
            for x in matched
        }

        # A genuine SOP header normally has several
        # structural fields.
        if len(fields) >= 3:

            candidates.append({
                "row_index": row_index,
                "row": row,
                "matched": matched,
                "fields": sorted(fields)
            })

    if not candidates:
        return None

    # Prefer the candidate with most structural fields.
    candidates.sort(
        key=lambda x: (
            len(x["fields"]),
            -x["row"]["top"]
        ),
        reverse=True
    )

    return candidates[0]


# ============================================================
# ESTIMATE COLUMN ANCHORS
# ============================================================

def estimate_column_anchors(header):

    anchors = {}

    for item in header["matched"]:

        field = item["field"]
        word = item["word"]

        x = (
            word.get("left", 0)
            + word.get("right", 0)
        ) / 2

        if field not in anchors:

            anchors[field] = []

        anchors[field].append(x)

    result = {}

    for field, values in anchors.items():

        result[field] = (
            statistics.mean(values)
        )

    return result


# ============================================================
# ASSIGN WORD TO COLUMN
# ============================================================

def assign_word_to_column(
    word,
    anchors
):

    if not anchors:
        return None, 0

    center = (
        word.get("left", 0)
        + word.get("right", 0)
    ) / 2

    ordered = sorted(
        anchors.items(),
        key=lambda x: x[1]
    )

    # Determine midpoint boundaries.
    boundaries = []

    for index in range(
        len(ordered) - 1
    ):

        left_field, left_x = ordered[index]
        right_field, right_x = ordered[
            index + 1
        ]

        boundaries.append({
            "left_field": left_field,
            "right_field": right_field,
            "mid": (
                left_x + right_x
            ) / 2
        })

    if not boundaries:

        field = ordered[0][0]

        return field, 0.5

    if center < boundaries[0]["mid"]:

        return ordered[0][0], 0.75

    for boundary in boundaries:

        if center < boundary["mid"]:

            return (
                boundary["left_field"],
                0.80
            )

    return (
        ordered[-1][0],
        0.75
    )


# ============================================================
# ROW COLUMN RECONSTRUCTION
# ============================================================

def reconstruct_row(
    row,
    anchors
):

    buckets = {}

    word_assignments = []

    for word in row["words"]:

        field, confidence = (
            assign_word_to_column(
                word,
                anchors
            )
        )

        if not field:
            continue

        text = clean(
            word.get(
                "text",
                ""
            )
        )

        if not text:
            continue

        buckets.setdefault(
            field,
            []
        ).append(text)

        word_assignments.append({
            "text": text,
            "field": field,
            "assignment_confidence": confidence,
            "left": word.get(
                "left",
                0
            ),
            "top": word.get(
                "top",
                0
            ),
            "confidence": word.get(
                "confidence",
                -1
            )
        })

    values = {}

    for field, tokens in buckets.items():

        values[field] = clean(
            " ".join(tokens)
        )

    return {
        "source_row": row["text"],
        "top": row["top"],
        "values": values,
        "word_assignments": word_assignments
    }


# ============================================================
# DETECT PROCEDURE NUMBER
# ============================================================

def extract_step(text):

    normalized = clean(
        text
    )

    # Only accept a number at the beginning.
    match = re.match(
        r"^\s*(\d{1,2})\s*[\.\)\-:]?\s+",
        normalized
    )

    if not match:
        return None

    number = int(
        match.group(1)
    )

    # SOP procedures are normally limited.
    # Reject absurd document-page numbering.
    if number < 1 or number > 50:
        return None

    return number


# ============================================================
# PROCESS PAGES
# ============================================================

page_results = []

global_headers = []

for page in data.get(
    "pages",
    []
):

    page_number = page.get(
        "page"
    )

    rows = build_rows(
        page
    )

    header = detect_table_header(
        rows
    )

    page_result = {
        "page": page_number,
        "row_count": len(rows),
        "header": None,
        "columns": {},
        "table_rows": []
    }

    if header:

        anchors = estimate_column_anchors(
            header
        )

        page_result["header"] = {
            "row_index": header["row_index"],
            "text": header["row"]["text"],
            "fields": header["fields"],
            "matched": [
                {
                    "field": x["field"],
                    "score": x["score"],
                    "text": x["word"].get(
                        "text",
                        ""
                    ),
                    "x": (
                        x["word"].get(
                            "left",
                            0
                        )
                        + x["word"].get(
                            "right",
                            0
                        )
                    ) / 2
                }
                for x in header["matched"]
            ]
        }

        page_result["columns"] = anchors

        global_headers.append({
            "page": page_number,
            "fields": header["fields"],
            "anchors": anchors
        })

        # ----------------------------------------------------
        # Rows below the header are candidates.
        # ----------------------------------------------------

        for row in rows[
            header["row_index"] + 1:
        ]:

            reconstructed = reconstruct_row(
                row,
                anchors
            )

            step = extract_step(
                row["text"]
            )

            # Require a real activity column if
            # possible. This avoids legal basis false positives.
            activity = reconstructed[
                "values"
            ].get(
                "activity",
                ""
            )

            number_value = reconstructed[
                "values"
            ].get(
                "no",
                ""
            )

            # Accept row only if it has table-like evidence.
            table_evidence = 0

            if activity:
                table_evidence += 1

            if number_value:
                table_evidence += 1

            if reconstructed[
                "values"
            ].get("time"):
                table_evidence += 1

            if reconstructed[
                "values"
            ].get("output"):
                table_evidence += 1

            if table_evidence >= 1:

                reconstructed[
                    "step_candidate"
                ] = step

                reconstructed[
                    "table_evidence_score"
                ] = table_evidence

                page_result[
                    "table_rows"
                ].append(
                    reconstructed
                )

    page_results.append(
        page_result
    )


# ============================================================
# MERGE PROCEDURE CANDIDATES
# ============================================================

procedure_candidates = []

for page in page_results:

    for row in page[
        "table_rows"
    ]:

        values = row[
            "values"
        ]

        activity = clean(
            values.get(
                "activity",
                ""
            )
        )

        if not activity:
            continue

        step = row.get(
            "step_candidate"
        )

        # Only use an explicitly reconstructed number.
        # Never manufacture a step number.
        if step is None:
            continue

        procedure_candidates.append({
            "step": step,
            "activity": activity,
            "actor": clean(
                values.get(
                    "actor",
                    ""
                )
            ),
            "requirement": clean(
                values.get(
                    "requirement",
                    ""
                )
            ),
            "time": clean(
                values.get(
                    "time",
                    ""
                )
            ),
            "output": clean(
                values.get(
                    "output",
                    ""
                )
            ),
            "quality": clean(
                values.get(
                    "quality",
                    ""
                )
            ),
            "note": clean(
                values.get(
                    "note",
                    ""
                )
            ),
            "evidence": {
                "page": page["page"],
                "source_row": row[
                    "source_row"
                ],
                "top": row["top"]
            }
        })


# ============================================================
# DEDUPLICATE
# ============================================================

deduplicated = {}

for item in procedure_candidates:

    step = item["step"]

    if step not in deduplicated:

        deduplicated[
            step
        ] = item

    else:

        current = deduplicated[
            step
        ]

        # Prefer row containing more populated
        # structural fields.
        current_score = sum(
            bool(
                current.get(field)
            )
            for field in [
                "activity",
                "actor",
                "requirement",
                "time",
                "output"
            ]
        )

        new_score = sum(
            bool(
                item.get(field)
            )
            for field in [
                "activity",
                "actor",
                "requirement",
                "time",
                "output"
            ]
        )

        if new_score > current_score:

            deduplicated[
                step
            ] = item


procedure = [
    deduplicated[key]
    for key in sorted(
        deduplicated
    )
]


# ============================================================
# QUALITY GATE
# ============================================================

warnings = []

if not global_headers:

    warnings.append(
        "NO_STRUCTURED_TABLE_HEADER_DETECTED"
    )

if not procedure:

    warnings.append(
        "NO_SAFE_PROCEDURE_ROWS_RECONSTRUCTED"
    )

steps = [
    x["step"]
    for x in procedure
]

if steps:

    expected = set(
        range(
            min(steps),
            max(steps) + 1
        )
    )

    missing = sorted(
        expected - set(steps)
    )

else:

    missing = []

if missing:

    warnings.append(
        "PROCEDURE_STEP_GAPS:"
        + ",".join(
            str(x)
            for x in missing
        )
    )

# ------------------------------------------------------------
# Critical safety checks
# ------------------------------------------------------------

for item in procedure:

    text = normalize(
        item["activity"]
    )

    if any(
        term in text
        for term in [
            "undang-undang",
            "peraturan menteri",
            "peraturan pemerintah",
            "peraturan presiden",
            "peraturan daerah"
        ]
    ):

        warnings.append(
            f"LEGAL_TEXT_IN_ACTIVITY_STEP_{item['step']}"
        )

    if any(
        term in text
        for term in [
            "fcktp",
            "kartu keluarga",
            "buku nikah",
            "sptjm",
            "alamat email"
        ]
    ):

        warnings.append(
            f"REQUIREMENT_TEXT_IN_ACTIVITY_STEP_{item['step']}"
        )

# ------------------------------------------------------------
# Confidence
# ------------------------------------------------------------

if procedure:

    field_population = []

    for item in procedure:

        fields = [
            "activity",
            "actor",
            "requirement",
            "time",
            "output"
        ]

        populated = sum(
            bool(item[field])
            for field in fields
        )

        field_population.append(
            populated / len(fields)
        )

    structural_confidence = (
        sum(field_population)
        / len(field_population)
    )

else:

    structural_confidence = 0.0


if structural_confidence < 0.35:

    warnings.append(
        "LOW_STRUCTURAL_CONFIDENCE"
    )


# Governance status.
#
# Even with no warnings, this is NOT verified.
#
if warnings:

    status = "REVIEW_REQUIRED"

else:

    status = "READY_FOR_HUMAN_VALIDATION"


# ============================================================
# RESULT
# ============================================================

result = {

    "schema_version": "2.0",

    "document_type": "SOP_TTE",

    "governance": {

        "status": status,

        "source_verification":
            "PENDING",

        "content_verification":
            "PENDING",

        "human_validation_required":
            True,

        "automatic_verification":
            False,

        "production_ingestion_allowed":
            False
    },

    "source": {

        "layout_file": str(
            INPUT.relative_to(ROOT)
        ),

        "layout_sha256":
            layout_hash
    },

    "engine": {

        "name": ENGINE,

        "version": VERSION,

        "generated_at":
            now_utc()
    },

    "table": {

        "headers":
            global_headers,

        "pages":
            page_results,

        "procedure_candidates":
            procedure,

        "structural_confidence":
            round(
                structural_confidence,
                4
            )
    },

    "warnings":
        sorted(
            set(warnings)
        )
}


OUTPUT.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


# ============================================================
# REPORT
# ============================================================

report = {

    "engine": ENGINE,

    "version": VERSION,

    "generated_at":
        now_utc(),

    "input": {

        "file": str(
            INPUT.relative_to(ROOT)
        ),

        "sha256":
            layout_hash
    },

    "result": {

        "status":
            status,

        "pages":
            len(page_results),

        "headers":
            len(global_headers),

        "procedure_candidates":
            len(procedure),

        "steps":
            steps,

        "missing_steps":
            missing,

        "structural_confidence":
            round(
                structural_confidence,
                4
            ),

        "warnings":
            sorted(
                set(warnings)
            )
    },

    "governance": {

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


REPORT.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


# ============================================================
# CONSOLE
# ============================================================

print()
print("=" * 78)
print("RECONSTRUCTION V2 RESULT")
print("=" * 78)

print(
    f"STATUS              : {status}"
)

print(
    f"TABLE HEADERS       : {len(global_headers)}"
)

print(
    f"PROCEDURE CANDIDATES: {len(procedure)}"
)

print(
    f"STRUCTURAL CONF     : "
    f"{structural_confidence:.4f}"
)

print()

print("DETECTED TABLE HEADERS")

if global_headers:

    for header in global_headers:

        print(
            f"  PAGE {header['page']} : "
            f"{', '.join(header['fields'])}"
        )

else:

    print(
        "  NONE"
    )

print()

print("SAFE PROCEDURE CANDIDATES")

if procedure:

    for item in procedure:

        print(
            f"  STEP {item['step']:02d}"
        )

        print(
            f"    ACTIVITY    : "
            f"{item['activity']}"
        )

        print(
            f"    ACTOR       : "
            f"{item['actor'] or '-'}"
        )

        print(
            f"    REQUIREMENT : "
            f"{item['requirement'] or '-'}"
        )

        print(
            f"    TIME        : "
            f"{item['time'] or '-'}"
        )

        print(
            f"    OUTPUT      : "
            f"{item['output'] or '-'}"
        )

else:

    print(
        "  NONE"
    )

print()

print("WARNINGS")

if warnings:

    for warning in sorted(
        set(warnings)
    ):

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
    "  Original PDF : NOT MODIFIED"
)

print(
    "  OCR Evidence : NOT MODIFIED"
)

print(
    "  Production DB: NOT TOUCHED"
)

print(
    "  Verification : NOT AUTOMATIC"
)

print(
    "  Human Review : REQUIRED"
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
