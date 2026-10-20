from pathlib import Path
import json
import hashlib
import datetime
import pymupdf

ROOT = Path.cwd()

PDF = ROOT / "data" / "knowledge" / "sop" / "original" / "CAPIL_02_(1).pdf"
OCR_LAYOUT = ROOT / "data" / "knowledge" / "sop" / "extracted" / "CAPIL_02_GOVERNANCE_OCR" / "layout.json"

OUT = ROOT / "data" / "knowledge" / "sop" / "extracted" / "CAPIL_02_GOVERNANCE_OCR" / "pdf_geometry"

OUT.mkdir(parents=True, exist_ok=True)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

print("=" * 78)
print("NUSANTARA SOP PDF GEOMETRY INSPECTOR")
print("=" * 78)

print(f"PDF        : {PDF}")
print(f"OCR LAYOUT : {OCR_LAYOUT}")

if not PDF.exists():
    raise SystemExit("PDF asli tidak ditemukan.")

if not OCR_LAYOUT.exists():
    raise SystemExit("layout.json tidak ditemukan.")

pdf_hash = sha256(PDF)

ocr = json.loads(
    OCR_LAYOUT.read_text(encoding="utf-8")
)

doc = pymupdf.open(PDF)

pages = []

for page_index in range(len(doc)):

    page = doc[page_index]

    drawings = page.get_drawings()

    lines = []
    rectangles = []
    other = []

    for drawing_index, drawing in enumerate(drawings):

        rect = drawing.get("rect")

        if not rect:
            continue

        items = drawing.get("items", [])

        drawing_info = {
            "drawing_index": drawing_index,
            "rect": {
                "x0": rect.x0,
                "y0": rect.y0,
                "x1": rect.x1,
                "y1": rect.y1
            },
            "items": []
        }

        for item in items:

            kind = item[0]

            if kind == "l":

                p1 = item[1]
                p2 = item[2]

                line = {
                    "x1": p1.x,
                    "y1": p1.y,
                    "x2": p2.x,
                    "y2": p2.y
                }

                drawing_info["items"].append(
                    {
                        "type": "line",
                        **line
                    }
                )

                dx = abs(p2.x - p1.x)
                dy = abs(p2.y - p1.y)

                if dx >= 20 or dy >= 20:
                    lines.append(line)

            elif kind == "re":

                r = item[1]

                rectangle = {
                    "x0": r.x0,
                    "y0": r.y0,
                    "x1": r.x1,
                    "y1": r.y1,
                    "width": r.width,
                    "height": r.height
                }

                drawing_info["items"].append(
                    {
                        "type": "rectangle",
                        **rectangle
                    }
                )

                rectangles.append(
                    rectangle
                )

            else:

                drawing_info["items"].append(
                    {
                        "type": str(kind)
                    }
                )

        if drawing_info["items"]:
            other.append(drawing_info)

    horizontal = []
    vertical = []

    for line in lines:

        dx = abs(
            line["x2"] - line["x1"]
        )

        dy = abs(
            line["y2"] - line["y1"]
        )

        if dx >= 20 and dy <= 3:
            horizontal.append(line)

        elif dy >= 20 and dx <= 3:
            vertical.append(line)

    horizontal.sort(
        key=lambda x: (
            min(x["y1"], x["y2"]),
            min(x["x1"], x["x2"])
        )
    )

    vertical.sort(
        key=lambda x: (
            min(x["x1"], x["x2"]),
            min(x["y1"], x["y2"])
        )
    )

    pages.append(
        {
            "page": page_index + 1,

            "page_size": {
                "width": page.rect.width,
                "height": page.rect.height
            },

            "drawing_count": len(drawings),

            "line_count": len(lines),

            "horizontal_lines": horizontal,

            "vertical_lines": vertical,

            "rectangle_count": len(rectangles),

            "rectangles": rectangles,

            "drawings": other
        }
    )

doc.close()

result = {
    "schema_version": "1.0",

    "engine": {
        "name": "Nusantara SOP PDF Geometry Inspector",
        "version": "1.0",
        "generated_at": now()
    },

    "source": {
        "pdf": str(PDF.relative_to(ROOT)),
        "pdf_sha256": pdf_hash,
        "ocr_layout": str(OCR_LAYOUT.relative_to(ROOT))
    },

    "pages": pages,

    "governance": {
        "original_pdf_modified": False,
        "ocr_modified": False,
        "production_db_modified": False,
        "interpretation": False,
        "verification": False,
        "human_review_required": True
    }
}

output = OUT / "pdf_geometry.json"

output.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print()
print("=" * 78)
print("PDF GEOMETRY RESULT")
print("=" * 78)

for page in pages:

    print(
        f"PAGE {page['page']}: "
        f"drawings={page['drawing_count']} "
        f"lines={page['line_count']} "
        f"H={len(page['horizontal_lines'])} "
        f"V={len(page['vertical_lines'])} "
        f"rectangles={page['rectangle_count']}"
    )

print()
print("OUTPUT")
print(output)

print()
print("GOVERNANCE")
print("  Original PDF : NOT MODIFIED")
print("  OCR Evidence : NOT MODIFIED")
print("  Production DB: NOT TOUCHED")
print("  Interpretation: DISABLED")
print("  Verification : DISABLED")
print("  Human Review : REQUIRED")

print("=" * 78)
