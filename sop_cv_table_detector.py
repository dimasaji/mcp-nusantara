from pathlib import Path
import sys
import json
import cv2
import numpy as np
import datetime
import hashlib

ROOT = Path.cwd()

BASE = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
    / "extracted"
    / "CAPIL_02_GOVERNANCE_OCR"
)

OUT = BASE / "table_vision"

OUT.mkdir(parents=True, exist_ok=True)

print("=" * 78)
print("NUSANTARA SOP COMPUTER VISION TABLE DETECTOR")
print("=" * 78)
print("ENGINE VERSION : 1.1 FIXED")
print(f"INPUT          : {BASE}")
print(f"OUTPUT         : {OUT}")


def now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b""
        ):
            h.update(chunk)

    return h.hexdigest()


def cluster_positions(values, tolerance=12):
    if not values:
        return []

    values = sorted(
        int(v)
        for v in values
    )

    clusters = [[values[0]]]

    for value in values[1:]:
        current = clusters[-1]

        if abs(
            value - int(np.mean(current))
        ) <= tolerance:
            current.append(value)
        else:
            clusters.append([value])

    return [
        int(round(np.mean(cluster)))
        for cluster in clusters
    ]


def merge_segments(
    segments,
    axis="horizontal",
    tolerance=12
):
    if not segments:
        return []

    normalized = []

    for x1, y1, x2, y2 in segments:

        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        if axis == "horizontal":

            y = int(round((y1 + y2) / 2))
            start = min(x1, x2)
            end = max(x1, x2)

            normalized.append(
                (start, end, y)
            )

        else:

            x = int(round((x1 + x2) / 2))
            start = min(y1, y2)
            end = max(y1, y2)

            normalized.append(
                (start, end, x)
            )

    normalized.sort()

    merged = []

    for item in normalized:

        if not merged:
            merged.append(item)
            continue

        previous = merged[-1]

        if axis == "horizontal":

            ps, pe, py = previous
            cs, ce, cy = item

            same_row = abs(py - cy) <= tolerance
            overlap = cs <= pe + tolerance

            if same_row and overlap:

                merged[-1] = (
                    min(ps, cs),
                    max(pe, ce),
                    int(round((py + cy) / 2))
                )

            else:
                merged.append(item)

        else:

            ps, pe, px = previous
            cs, ce, cx = item

            same_col = abs(px - cx) <= tolerance
            overlap = cs <= pe + tolerance

            if same_col and overlap:

                merged[-1] = (
                    min(ps, cs),
                    max(pe, ce),
                    int(round((px + cx) / 2))
                )

            else:
                merged.append(item)

    return merged


def extract_hough_line(item):
    """
    Robustly normalize every possible OpenCV HoughLinesP
    return shape into x1,y1,x2,y2.
    """

    arr = np.asarray(item).reshape(-1)

    if arr.size < 4:
        return None

    try:
        return (
            int(arr[0]),
            int(arr[1]),
            int(arr[2]),
            int(arr[3])
        )
    except Exception:
        return None


# ============================================================
# FIND PAGE IMAGES
# ============================================================

images = sorted(
    BASE.glob("page_*.png")
)

if not images:
    images = sorted(
        BASE.rglob("*.png")
    )

if not images:

    print()
    print("ERROR: PNG halaman tidak ditemukan.")
    print(BASE)
    sys.exit(2)

print()
print(f"PAGE IMAGES    : {len(images)}")


# ============================================================
# PROCESS PAGES
# ============================================================

all_pages = []

for image_path in images:

    print()
    print(f"PROCESS : {image_path.name}")

    image = cv2.imread(
        str(image_path),
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:

        print("  STATUS     : FAILED TO READ IMAGE")

        continue

    height, width = image.shape

    print(
        f"  SIZE       : {width} x {height}"
    )

    # --------------------------------------------------------
    # Threshold
    # --------------------------------------------------------

    binary = cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        15
    )

    # --------------------------------------------------------
    # Morphological extraction
    # --------------------------------------------------------

    horizontal_length = max(
        40,
        width // 15
    )

    vertical_length = max(
        40,
        height // 15
    )

    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            horizontal_length,
            1
        )
    )

    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            1,
            vertical_length
        )
    )

    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        horizontal_kernel
    )

    vertical = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        vertical_kernel
    )

    # --------------------------------------------------------
    # Hough
    # --------------------------------------------------------

    horizontal_raw = cv2.HoughLinesP(
        horizontal,
        1,
        np.pi / 180,
        threshold=max(
            30,
            width // 20
        ),
        minLineLength=max(
            40,
            width // 20
        ),
        maxLineGap=25
    )

    vertical_raw = cv2.HoughLinesP(
        vertical,
        1,
        np.pi / 180,
        threshold=max(
            30,
            height // 20
        ),
        minLineLength=max(
            40,
            height // 20
        ),
        maxLineGap=25
    )

    horizontal_segments = []
    vertical_segments = []

    # --------------------------------------------------------
    # SAFE HORIZONTAL PARSE
    # --------------------------------------------------------

    if horizontal_raw is not None:

        for item in horizontal_raw:

            line = extract_hough_line(item)

            if line is None:
                continue

            x1, y1, x2, y2 = line

            if abs(y2 - y1) <= 8:

                horizontal_segments.append(
                    line
                )

    # --------------------------------------------------------
    # SAFE VERTICAL PARSE
    # --------------------------------------------------------

    if vertical_raw is not None:

        for item in vertical_raw:

            line = extract_hough_line(item)

            if line is None:
                continue

            x1, y1, x2, y2 = line

            if abs(x2 - x1) <= 8:

                vertical_segments.append(
                    line
                )

    horizontal_lines = merge_segments(
        horizontal_segments,
        "horizontal"
    )

    vertical_lines = merge_segments(
        vertical_segments,
        "vertical"
    )

    horizontal_positions = cluster_positions(
        [
            item[2]
            for item in horizontal_lines
        ]
    )

    vertical_positions = cluster_positions(
        [
            item[2]
            for item in vertical_lines
        ]
    )

    # --------------------------------------------------------
    # Diagnostic image
    # --------------------------------------------------------

    diagnostic = cv2.cvtColor(
        image,
        cv2.COLOR_GRAY2BGR
    )

    for x1, x2, y in horizontal_lines:

        cv2.line(
            diagnostic,
            (x1, y),
            (x2, y),
            (0, 0, 255),
            3
        )

    for y1, y2, x in vertical_lines:

        cv2.line(
            diagnostic,
            (x, y1),
            (x, y2),
            (255, 0, 0),
            3
        )

    diagnostic_path = (
        OUT
        / f"{image_path.stem}_detected.png"
    )

    cv2.imwrite(
        str(diagnostic_path),
        diagnostic
    )

    page_result = {

        "page_image":
            image_path.name,

        "sha256":
            sha256(image_path),

        "width":
            width,

        "height":
            height,

        "horizontal_line_count":
            len(horizontal_lines),

        "vertical_line_count":
            len(vertical_lines),

        "horizontal_positions":
            horizontal_positions,

        "vertical_positions":
            vertical_positions,

        "horizontal_segments":
            [
                {
                    "start": x1,
                    "end": x2,
                    "y": y
                }
                for x1, x2, y
                in horizontal_lines
            ],

        "vertical_segments":
            [
                {
                    "start": y1,
                    "end": y2,
                    "x": x
                }
                for y1, y2, x
                in vertical_lines
            ],

        "diagnostic_image":
            str(
                diagnostic_path.relative_to(ROOT)
            )
    }

    all_pages.append(
        page_result
    )

    print(
        f"  HORIZONTAL : "
        f"{len(horizontal_lines)}"
    )

    print(
        f"  VERTICAL   : "
        f"{len(vertical_lines)}"
    )

    print(
        f"  H POS      : "
        f"{horizontal_positions}"
    )

    print(
        f"  V POS      : "
        f"{vertical_positions}"
    )


# ============================================================
# TABLE CANDIDATES
# ============================================================

table_candidates = []

for page in all_pages:

    h = page[
        "horizontal_positions"
    ]

    v = page[
        "vertical_positions"
    ]

    if len(h) >= 3 and len(v) >= 3:

        table_candidates.append(
            page["page_image"]
        )


# ============================================================
# MASTER
# ============================================================

result = {

    "schema_version": "1.1",

    "engine": {
        "name":
            "Nusantara SOP Computer Vision Table Detector",
        "version":
            "1.1-fixed",
        "generated_at":
            now()
    },

    "input": {
        "directory":
            str(BASE.relative_to(ROOT))
    },

    "pages":
        all_pages,

    "table_candidates":
        table_candidates,

    "governance": {

        "original_pdf_modified":
            False,

        "ocr_evidence_modified":
            False,

        "interpretation":
            False,

        "verification":
            False,

        "production_db_modified":
            False,

        "human_review_required":
            True
    }
}

master = OUT / "table_vision.json"

master.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


print()
print("=" * 78)
print("TABLE VISION RESULT")
print("=" * 78)

print(
    f"PAGES PROCESSED  : {len(all_pages)}"
)

print(
    f"TABLE CANDIDATES : {len(table_candidates)}"
)

if table_candidates:

    for page in table_candidates:

        print(
            f"  TABLE CANDIDATE : {page}"
        )

else:

    print(
        "  NO STRONG TABLE GRID DETECTED"
    )

print()
print("OUTPUT")
print(
    f"  {master}"
)

print()
print("GOVERNANCE")
print("  Original PDF : NOT MODIFIED")
print("  OCR Evidence : NOT MODIFIED")
print("  Interpretation: DISABLED")
print("  Verification : DISABLED")
print("  Production DB: NOT TOUCHED")
print("  Human Review : REQUIRED")

print("=" * 78)
