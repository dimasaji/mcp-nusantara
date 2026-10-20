from pathlib import Path
import json
import hashlib
import datetime
import fitz
import re

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
    / "extracted"
    / "CAPIL_02_GOVERNANCE_OCR"
    / "visual_inspection"
)

OUT.mkdir(
    parents=True,
    exist_ok=True
)

print("=" * 78)
print("NUSANTARA SOP VISUAL EVIDENCE INSPECTOR")
print("=" * 78)

if not INPUT.exists():
    raise SystemExit(
        f"Input tidak ditemukan:\n{INPUT}"
    )

data = json.loads(
    INPUT.read_text(
        encoding="utf-8"
    )
)

# ============================================================
# HELPERS
# ============================================================

def clean(text):
    return re.sub(
        r"\s+",
        " ",
        str(text or "")
    ).strip()


def sha256(path):

    h = hashlib.sha256()

    with path.open("rb") as f:

        while True:

            block = f.read(
                1024 * 1024
            )

            if not block:
                break

            h.update(block)

    return h.hexdigest()


# ============================================================
# CREATE VISUAL INSPECTION DATA
# ============================================================

inspection = {
    "schema_version": "1.0",

    "engine": {
        "name": "Nusantara SOP Visual Evidence Inspector",
        "version": "1.0",
        "generated_at": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
    },

    "governance": {
        "interpretation": False,
        "verification": False,
        "production_ingestion": False,
        "human_validation_required": True
    },

    "source": {
        "layout": str(
            INPUT.relative_to(ROOT)
        ),
        "layout_sha256": sha256(INPUT)
    },

    "pages": []
}


# ============================================================
# VISUAL PAGE GENERATION
# ============================================================

for page_data in data.get(
    "pages",
    []
):

    page_number = page_data.get(
        "page"
    )

    image_relative = page_data.get(
        "image"
    )

    image_path = ROOT / image_relative

    if not image_path.exists():

        print(
            f"PAGE {page_number}: image tidak ditemukan"
        )

        continue

    # --------------------------------------------------------
    # Open OCR image
    # --------------------------------------------------------

    image = fitz.Pixmap(
        str(image_path)
    )

    width = image.width
    height = image.height

    # --------------------------------------------------------
    # Create SVG overlay
    # --------------------------------------------------------

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )

    # Background
    svg.append(
        f'<image href="page_{page_number:03d}.png" '
        f'x="0" y="0" width="{width}" '
        f'height="{height}" '
        f'preserveAspectRatio="none"/>'
    )

    # --------------------------------------------------------
    # Horizontal guide every 100 px
    # --------------------------------------------------------

    for y in range(
        0,
        height,
        100
    ):

        svg.append(
            f'<line x1="0" y1="{y}" '
            f'x2="{width}" y2="{y}" '
            f'stroke="red" '
            f'stroke-width="1" '
            f'stroke-opacity="0.20"/>'
        )

        svg.append(
            f'<text x="5" y="{y + 14}" '
            f'font-size="12" '
            f'fill="red">{y}</text>'
        )

    # --------------------------------------------------------
    # Vertical guide every 100 px
    # --------------------------------------------------------

    for x in range(
        0,
        width,
        100
    ):

        svg.append(
            f'<line x1="{x}" y1="0" '
            f'x2="{x}" y2="{height}" '
            f'stroke="blue" '
            f'stroke-width="1" '
            f'stroke-opacity="0.20"/>'
        )

        svg.append(
            f'<text x="{x + 3}" y="15" '
            f'font-size="12" '
            f'fill="blue">{x}</text>'
        )

    # --------------------------------------------------------
    # OCR word boxes
    # --------------------------------------------------------

    words = page_data.get(
        "words",
        []
    )

    for index, word in enumerate(
        words
    ):

        left = int(
            word.get(
                "left",
                0
            )
        )

        top = int(
            word.get(
                "top",
                0
            )
        )

        word_width = int(
            word.get(
                "width",
                0
            )
        )

        word_height = int(
            word.get(
                "height",
                0
            )
        )

        confidence = float(
            word.get(
                "confidence",
                -1
            )
        )

        text = clean(
            word.get(
                "text",
                ""
            )
        )

        # Different visual indication based on confidence.
        if confidence >= 80:
            stroke = "green"
        elif confidence >= 60:
            stroke = "orange"
        else:
            stroke = "red"

        svg.append(
            f'<rect x="{left}" y="{top}" '
            f'width="{word_width}" '
            f'height="{word_height}" '
            f'fill="none" '
            f'stroke="{stroke}" '
            f'stroke-width="1"/>'
        )

        # Only label lower confidence OCR
        # to keep visual inspection usable.
        if confidence < 60:

            svg.append(
                f'<text '
                f'x="{left}" '
                f'y="{max(10, top - 2)}" '
                f'font-size="10" '
                f'fill="red">'
                f'{confidence:.0f}'
                f'</text>'
            )

    svg.append(
        "</svg>"
    )

    svg_text = "\n".join(
        svg
    )

    svg_file = (
        OUT
        / f"page_{page_number:03d}_inspection.svg"
    )

    svg_file.write_text(
        svg_text,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Generate a coordinate report
    # --------------------------------------------------------

    rows = {}

    for word in words:

        block = word.get(
            "block_num",
            0
        )

        paragraph = word.get(
            "par_num",
            0
        )

        line = word.get(
            "line_num",
            0
        )

        key = (
            block,
            paragraph,
            line
        )

        rows.setdefault(
            key,
            []
        ).append(word)

    row_data = []

    for key, row_words in rows.items():

        row_words.sort(
            key=lambda x: x.get(
                "left",
                0
            )
        )

        row_text = clean(
            " ".join(
                w.get(
                    "text",
                    ""
                )
                for w in row_words
            )
        )

        if not row_text:
            continue

        row_data.append({
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
            "text": row_text,
            "words": [
                {
                    "text": w.get(
                        "text",
                        ""
                    ),
                    "left": w.get(
                        "left",
                        0
                    ),
                    "top": w.get(
                        "top",
                        0
                    ),
                    "right": w.get(
                        "right",
                        0
                    ),
                    "bottom": w.get(
                        "bottom",
                        0
                    ),
                    "confidence": w.get(
                        "confidence",
                        -1
                    )
                }
                for w in row_words
            ]
        })

    row_data.sort(
        key=lambda x: (
            x["top"],
            x["left"]
        )
    )

    rows_file = (
        OUT
        / f"page_{page_number:03d}_rows.json"
    )

    rows_file.write_text(
        json.dumps(
            row_data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    inspection["pages"].append({
        "page": page_number,
        "width": width,
        "height": height,
        "words": len(words),
        "rows": len(row_data),
        "visual_overlay": str(
            svg_file.relative_to(ROOT)
        ),
        "row_evidence": str(
            rows_file.relative_to(ROOT)
        )
    })

    print(
        f"PAGE {page_number}: "
        f"{len(words)} words / "
        f"{len(row_data)} rows"
    )


# ============================================================
# WRITE MASTER INSPECTION
# ============================================================

master = (
    OUT
    / "visual_inspection.json"
)

master.write_text(
    json.dumps(
        inspection,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print()
print("=" * 78)
print("VISUAL INSPECTION COMPLETE")
print("=" * 78)

print(
    f"OUTPUT : {OUT}"
)

print(
    f"MASTER : {master}"
)

print()
print("GOVERNANCE")
print("  PDF ORIGINAL       : NOT MODIFIED")
print("  OCR EVIDENCE       : NOT MODIFIED")
print("  PRODUCTION DB      : NOT TOUCHED")
print("  INTERPRETATION     : DISABLED")
print("  VERIFICATION       : DISABLED")
print("  HUMAN REVIEW       : REQUIRED")

print("=" * 78)
