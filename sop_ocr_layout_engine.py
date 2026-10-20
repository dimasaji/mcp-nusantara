from pathlib import Path
import json
import subprocess
import pymupdf
import pytesseract
from PIL import Image
from pytesseract import Output

PDF = Path("data/knowledge/sop/original/CAPIL_02_(1).pdf")
OUT = Path("data/knowledge/sop/extracted/CAPIL_02_LAYOUT")
OUT.mkdir(parents=True, exist_ok=True)

TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

print("=" * 72)
print("NUSANTARA OCR LAYOUT ENGINE")
print("=" * 72)
print(f"PDF       : {PDF}")
print(f"TESSERACT : {TESSERACT}")

if not PDF.exists():
    raise SystemExit(f"PDF tidak ditemukan: {PDF}")

if not Path(TESSERACT).exists():
    raise SystemExit(f"Tesseract tidak ditemukan: {TESSERACT}")

doc = pymupdf.open(PDF)

pages = []

for page_no, page in enumerate(doc, start=1):

    print()
    print(f"[PAGE {page_no}/{len(doc)}]")

    # --------------------------------------------------------
    # Render PDF menjadi image
    # --------------------------------------------------------

    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(2.5, 2.5),
        alpha=False
    )

    image = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    image_file = OUT / f"page_{page_no:03d}.png"
    image.save(image_file)

    print(f"  IMAGE : {image_file}")

    # --------------------------------------------------------
    # OCR dengan koordinat
    # --------------------------------------------------------

    data = pytesseract.image_to_data(
        image,
        lang="ind",
        config="--psm 6",
        output_type=Output.DICT
    )

    words = []

    total = len(data["text"])

    for i in range(total):

        raw = data["text"][i]
        text_value = (raw or "").strip()

        if not text_value:
            continue

        try:
            confidence = float(data["conf"][i])
        except Exception:
            confidence = -1

        if confidence < 0:
            continue

        words.append({
            "text": text_value,
            "confidence": round(confidence, 2),
            "left": int(data["left"][i]),
            "top": int(data["top"][i]),
            "width": int(data["width"][i]),
            "height": int(data["height"][i]),
            "right": int(data["left"][i]) + int(data["width"][i]),
            "bottom": int(data["top"][i]) + int(data["height"][i]),
            "block_num": int(data["block_num"][i]),
            "par_num": int(data["par_num"][i]),
            "line_num": int(data["line_num"][i]),
            "word_num": int(data["word_num"][i])
        })

    # --------------------------------------------------------
    # Rekonstruksi baris berdasarkan koordinat Y
    # --------------------------------------------------------

    words_sorted = sorted(
        words,
        key=lambda x: (
            x["top"],
            x["left"]
        )
    )

    rows = []

    y_tolerance = 12

    for word in words_sorted:

        assigned = None

        for row in rows:

            if abs(
                word["top"] - row["top"]
            ) <= y_tolerance:

                assigned = row
                break

        if assigned is None:

            assigned = {
                "top": word["top"],
                "words": []
            }

            rows.append(assigned)

        assigned["words"].append(word)

    # sort rows vertically
    rows.sort(
        key=lambda x: x["top"]
    )

    reconstructed_rows = []

    for row_index, row in enumerate(rows, start=1):

        row_words = sorted(
            row["words"],
            key=lambda x: x["left"]
        )

        row_text = " ".join(
            x["text"]
            for x in row_words
        )

        reconstructed_rows.append({
            "row": row_index,
            "top": row["top"],
            "text": row_text,
            "words": row_words
        })

    # --------------------------------------------------------
    # Detect approximate columns
    # --------------------------------------------------------

    page_width = image.width

    columns = {
        "left": 0,
        "quarter": round(page_width * 0.25),
        "half": round(page_width * 0.50),
        "three_quarter": round(page_width * 0.75),
        "right": page_width
    }

    # --------------------------------------------------------
    # Page result
    # --------------------------------------------------------

    page_result = {
        "page": page_no,
        "width": image.width,
        "height": image.height,
        "word_count": len(words),
        "row_count": len(reconstructed_rows),
        "columns": columns,
        "rows": reconstructed_rows
    }

    pages.append(page_result)

    output_page = OUT / f"page_{page_no:03d}.json"

    output_page.write_text(
        json.dumps(
            page_result,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(f"  WORDS : {len(words)}")
    print(f"  ROWS  : {len(reconstructed_rows)}")
    print(f"  JSON  : {output_page}")

doc.close()

# ============================================================
# GLOBAL OUTPUT
# ============================================================

result = {
    "engine": "Nusantara OCR Layout Engine",
    "version": "1.0",
    "source": str(PDF),
    "ocr": {
        "engine": "Tesseract 5.4",
        "language": "ind",
        "psm": 6,
        "coordinates": True
    },
    "pages": pages
}

output = OUT / "layout.json"

output.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print()
print("=" * 72)
print("OCR LAYOUT COMPLETE")
print("=" * 72)
print(f"PAGES     : {len(pages)}")
print(f"OUTPUT    : {output}")
print("DATABASE  : NOT TOUCHED")
print("=" * 72)
