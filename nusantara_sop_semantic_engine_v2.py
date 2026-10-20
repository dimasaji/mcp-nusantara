from pathlib import Path
import json
import re
import datetime

ROOT = Path.cwd()

INPUT_ROOT = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
    / "engine_output"
)

OUTPUT_ROOT = (
    ROOT
    / "data"
    / "knowledge"
    / "sop"
    / "semantic_output"
)

OUTPUT_ROOT.mkdir(
    parents=True,
    exist_ok=True
)


def now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def clean(text):
    return re.sub(
        r"\s+",
        " ",
        str(text or "")
    ).strip()


def normalize(text):
    return clean(text).lower()


def unique(items):
    result = []

    seen = set()

    for item in items:

        value = clean(item)

        if not value:
            continue

        key = normalize(value)

        if key not in seen:

            seen.add(key)

            result.append(value)

    return result


# ============================================================
# SOP NUMBER
# ============================================================

def detect_sop_number(
    text,
    filename
):

    patterns = [

        r"\bNO\s*SOP\s*[:\-]\s*([A-Z]{2,20}[-/][A-Z0-9./_-]+)",

        r"\bSOP\s*NO\s*[:\-]\s*([A-Z]{2,20}[-/][A-Z0-9./_-]+)",

        r"\bNO\s*[:\-]\s*([A-Z]{2,20}[-/][A-Z0-9./_-]+)"
    ]

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

    # filename fallback only when strongly recognizable
    match = re.search(
        r"\b([A-Z]{2,15}[-_]\d{1,4})\b",
        filename.upper()
    )

    if match:

        return match.group(1)

    return None


# ============================================================
# TITLE
# ============================================================

def detect_title(
    text
):

    patterns = [

        r"NAMA\s+SOP\s*[:\-]\s*([^\n|]+)",

        r"JUDUL\s+SOP\s*[:\-]\s*([^\n|]+)",

        r"NAMA\s+SOP\s+([^\n|]+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = clean(
                match.group(1)
            )

            # Reject obvious OCR contamination
            if (
                len(value) >= 10
                and
                len(value) <= 250
                and
                not value.lower().startswith(
                    (
                        "no sop",
                        "tgl",
                        "tanggal",
                        "bidang"
                    )
                )
            ):

                return value

    return None


# ============================================================
# SERVICE
# ============================================================

SERVICE_MAP = {

    "akta kelahiran":
        "akta_kelahiran",

    "kelahiran":
        "akta_kelahiran",

    "akta kematian":
        "akta_kematian",

    "kematian":
        "akta_kematian",

    "kartu keluarga":
        "kartu_keluarga",

    "ktp-el":
        "ktp_el",

    "ktp el":
        "ktp_el",

    "kia":
        "kia",

    "data pribadi":
        "data_pribadi",

    "data informasi administrasi kependudukan":
        "informasi_data_kependudukan",

    "informasi data penduduk":
        "informasi_data_penduduk"
}


def detect_service(
    title,
    text
):

    source = normalize(
        (title or "")
        + " "
        + text[:5000]
    )

    scores = {}

    for keyword, service in SERVICE_MAP.items():

        if keyword in source:

            scores[service] = (
                scores.get(
                    service,
                    0
                )
                + 1
            )

    if not scores:
        return None

    return max(
        scores,
        key=scores.get
    )


# ============================================================
# REQUIREMENT DETECTION
# ============================================================

REQUIREMENT_START = [
    "persyaratan",
    "kelengkapan",
    "persyaratan administrasi",
    "kelengkapan persyaratan"
]


REQUIREMENT_KEYWORDS = [

    "fc ktp",
    "fotokopi ktp",
    "fotocopy ktp",

    "fc kartu keluarga",
    "fotokopi kartu keluarga",
    "fotocopy kartu keluarga",

    "akta kelahiran",
    "akta perkawinan",
    "buku nikah",

    "surat keterangan",
    "surat pernyataan",

    "sp tjm",
    "sptjm",

    "nik",

    "alamat email",
    "nomor telepon",

    "dokumen",

    "formulir"
]


def is_requirement_candidate(
    text
):

    value = normalize(
        text
    )

    if len(value) < 4:
        return False

    if len(value) > 300:
        return False

    return any(
        keyword in value
        for keyword in REQUIREMENT_KEYWORDS
    )


def extract_requirements(
    pages
):

    results = []

    for page in pages:

        page_number = page.get(
            "page"
        )

        lines = page.get(
            "lines",
            []
        )

        for line in lines:

            text = clean(
                line.get(
                    "text"
                )
            )

            if not is_requirement_candidate(
                text
            ):
                continue

            lower = normalize(
                text
            )

            # Do not accept procedure-like sentences
            if any(
                phrase in lower
                for phrase in [
                    "menginput",
                    "memproses",
                    "mengajukan",
                    "memverifikasi",
                    "mencetak",
                    "menerima",
                    "mengambil",
                    "melakukan sertifikasi"
                ]
            ):
                continue

            results.append({

                "text":
                    text,

                "page":
                    page_number,

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
                    ),

                "evidence_type":
                    "OCR_LINE"
            })


    # Remove duplicates
    final = []

    seen = set()

    for item in results:

        key = normalize(
            item["text"]
        )

        if key in seen:
            continue

        seen.add(key)

        final.append(
            item
        )

    return final[:30]


# ============================================================
# TIME
# ============================================================

TIME_PATTERN = re.compile(

    r"\b\d+\s*"
    r"(?:menit|jam|hari kerja|hari)"
    r"\b",

    re.IGNORECASE
)


def extract_times(
    pages
):

    results = []

    for page in pages:

        text = page.get(
            "text",
            ""
        )

        for match in TIME_PATTERN.finditer(
            text
        ):

            value = clean(
                match.group(0)
            )

            if value not in [
                item["text"]
                for item in results
            ]:

                results.append({

                    "text":
                        value,

                    "page":
                        page.get(
                            "page"
                        ),

                    "evidence_type":
                        "OCR_TEXT"
                })

    return results


# ============================================================
# OUTPUT DETECTION
# ============================================================

OUTPUT_KEYWORDS = [

    "akta kelahiran",
    "akta kematian",
    "kartu keluarga",
    "kia",
    "ktp-el",
    "surat keterangan",
    "dokumen"
]


def extract_outputs(
    pages,
    title
):

    results = []

    title_lower = normalize(
        title or ""
    )

    for page in pages:

        text = normalize(
            page.get(
                "text",
                ""
            )
        )

        for keyword in OUTPUT_KEYWORDS:

            if keyword not in text:
                continue

            # Avoid simply declaring every document
            # mentioned in OCR as an output.
            output_phrases = [
                "tercetak",
                "diterima",
                "diserahkan",
                "hasil",
                "output",
                "menerima cetakan",
                "mencetak"
            ]

            if not any(
                phrase in text
                for phrase in output_phrases
            ):
                continue

            if (
                keyword == "ktp-el"
                and
                "ktp-el" not in title_lower
                and
                "ktp el" not in title_lower
            ):
                continue

            results.append({

                "text":
                    keyword,

                "page":
                    page.get(
                        "page"
                    ),

                "evidence_type":
                    "OUTPUT_CONTEXT"
            })

    final = []

    seen = set()

    for item in results:

        if item["text"] in seen:
            continue

        seen.add(
            item["text"]
        )

        final.append(
            item
        )

    return final


# ============================================================
# PROCEDURE
# ============================================================

PROCEDURE_VERBS = [

    "mengisi",
    "menyerahkan",
    "memeriksa",
    "memverifikasi",
    "memvalidasi",
    "menginput",
    "memproses",
    "menarik",
    "mengusulkan",
    "mengajukan",
    "melakukan",
    "mencetak",
    "menerima",
    "mengambil",
    "menandatangani",
    "mengirim",
    "meneruskan",
    "merekam"
]


def procedure_candidate(
    text
):

    lower = normalize(
        text
    )

    if len(text) < 12:
        return False

    if len(text) > 400:
        return False

    if not any(
        lower.startswith(
            verb
        )
        or
        (" " + verb + " ")
        in
        (" " + lower + " ")
        for verb in PROCEDURE_VERBS
    ):
        return False

    return True


def extract_procedure(
    pages
):

    results = []

    step_counter = 1

    for page in pages:

        for line in page.get(
            "lines",
            []
        ):

            text = clean(
                line.get(
                    "text"
                )
            )

            if not procedure_candidate(
                text
            ):
                continue

            # Exclude obvious metadata/legal text
            lower = normalize(
                text
            )

            if any(
                phrase in lower
                for phrase in [
                    "undang-undang",
                    "peraturan menteri",
                    "peraturan presiden",
                    "peraturan pemerintah",
                    "peraturan daerah",
                    "peraturan walikota"
                ]
            ):
                continue

            results.append({

                "step_candidate":
                    step_counter,

                "activity":
                    text,

                "page":
                    page.get(
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
                    ),

                "validated":
                    False
            })

            step_counter += 1

    return results


# ============================================================
# LEGAL BASIS
# ============================================================

LEGAL_PATTERNS = [

    r"Undang-Undang[^\n|]{5,180}",

    r"Peraturan Pemerintah[^\n|]{5,180}",

    r"Peraturan Presiden[^\n|]{5,180}",

    r"Peraturan Menteri[^\n|]{5,180}",

    r"Peraturan Daerah[^\n|]{5,180}",

    r"Peraturan Walikota[^\n|]{5,180}"
]


def extract_legal_basis(
    pages
):

    results = []

    for page in pages:

        text = page.get(
            "text",
            ""
        )

        for pattern in LEGAL_PATTERNS:

            for match in re.finditer(
                pattern,
                text,
                re.IGNORECASE
            ):

                value = clean(
                    match.group(0)
                )

                if len(value) > 220:
                    continue

                results.append({

                    "text":
                        value,

                    "page":
                        page.get(
                            "page"
                        ),

                    "evidence_type":
                        "LEGAL_BASIS"
                })


    final = []

    seen = set()

    for item in results:

        key = normalize(
            item["text"]
        )

        if key in seen:
            continue

        seen.add(key)

        final.append(
            item
        )

    return final


# ============================================================
# QUALITY GATE
# ============================================================

def quality_gate(
    document
):

    warnings = []

    errors = []


    identity = document[
        "identity"
    ]


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


    if not document.get(
        "service"
    ):
        warnings.append(
            "SERVICE_NOT_DETECTED"
        )


    req_count = len(
        document.get(
            "requirements",
            []
        )
    )


    if req_count > 15:
        warnings.append(
            "REQUIREMENT_COUNT_HIGH"
        )


    procedure_count = len(
        document.get(
            "procedure_candidates",
            []
        )
    )


    if procedure_count == 0:
        warnings.append(
            "NO_PROCEDURE_CANDIDATE"
        )


    if procedure_count > 50:
        warnings.append(
            "PROCEDURE_COUNT_HIGH_REVIEW"
        )


    if not document.get(
        "processing_time"
    ):
        warnings.append(
            "PROCESSING_TIME_NOT_DETECTED"
        )


    status = (
        "REVIEW_REQUIRED"
        if warnings
        else
        "READY_FOR_HUMAN_VALIDATION"
    )


    return {

        "status":
            status,

        "warnings":
            warnings,

        "errors":
            errors,

        "automatic_verification":
            False,

        "human_validation_required":
            True,

        "production_ingestion_allowed":
            False
    }


# ============================================================
# PROCESS DOCUMENT
# ============================================================

def process_document(
    structured_path
):

    data = json.loads(
        structured_path.read_text(
            encoding="utf-8"
        )
    )


    source = data.get(
        "source",
        {}
    )


    pages = data.get(
        "pages",
        []
    )


    filename = source.get(
        "source_file"
    ) or structured_path.parent.parent.parent.name


    all_text = "\n".join(
        page.get(
            "text",
            ""
        )
        for page in pages
    )


    title = detect_title(
        all_text
    )


    sop_number = detect_sop_number(
        all_text,
        filename
    )


    service = detect_service(
        title,
        all_text
    )


    requirements = extract_requirements(
        pages
    )


    procedure = extract_procedure(
        pages
    )


    times = extract_times(
        pages
    )


    outputs = extract_outputs(
        pages,
        title
    )


    legal_basis = extract_legal_basis(
        pages
    )


    document = {

        "schema_version":
            "2.0",

        "engine":
            {
                "name":
                    "Nusantara SOP Semantic Reconstruction Engine",

                "version":
                    "2.0",

                "generated_at":
                    now()
            },

        "identity":
            {
                "sop_number":
                    sop_number,

                "title":
                    title
            },

        "service":
            service,

        "requirements":
            requirements,

        "procedure_candidates":
            procedure,

        "processing_time":
            times,

        "outputs":
            outputs,

        "legal_basis":
            legal_basis,

        "source":
            source,

        "source_evidence":
            {
                "source_file":
                    filename,

                "pages":
                    len(pages),

                "ocr_words":
                    sum(
                        page.get(
                            "word_count",
                            0
                        )
                        for page in pages
                    ),

                "ocr_confidence":
                    round(
                        sum(
                            page.get(
                                "average_confidence",
                                0
                            )
                            for page in pages
                        )
                        /
                        max(
                            1,
                            len(pages)
                        ),
                        2
                    )
            }
    }


    quality = quality_gate(
        document
    )


    document[
        "quality_gate"
    ] = quality


    output_dir = (
        OUTPUT_ROOT
        / structured_path.parent.parent.parent.name
    )


    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    output_path = (
        output_dir
        / "semantic_sop.json"
    )


    output_path.write_text(
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


    return {

        "source_file":
            filename,

        "status":
            quality["status"],

        "sop_number":
            sop_number,

        "title":
            title,

        "service":
            service,

        "requirements":
            len(requirements),

        "procedure_candidates":
            len(procedure),

        "processing_time":
            len(times),

        "outputs":
            len(outputs),

        "legal_basis":
            len(legal_basis),

        "output":
            str(output_path),

        "warnings":
            quality["warnings"]
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 78)
    print(
        "NUSANTARA SOP SEMANTIC RECONSTRUCTION ENGINE"
    )
    print(
        "VERSION 2.0"
    )
    print("=" * 78)

    if not INPUT_ROOT.exists():

        raise SystemExit(
            f"Input tidak ditemukan: {INPUT_ROOT}"
        )


    files = list(
        INPUT_ROOT.glob(
            "*/structured/sop_structured.json"
        )
    )


    print(
        f"SOP STRUCTURED FILES : {len(files)}"
    )


    results = []


    for index, file in enumerate(
        sorted(files),
        start=1
    ):

        print()
        print(
            f"[{index}/{len(files)}] "
            f"{file.parent.parent.parent.name}"
        )


        try:

            result = process_document(
                file
            )

            results.append(
                result
            )


            print(
                f"  STATUS       : "
                f"{result['status']}"
            )

            print(
                f"  SOP NUMBER   : "
                f"{result['sop_number']}"
            )

            print(
                f"  TITLE        : "
                f"{result['title']}"
            )

            print(
                f"  SERVICE      : "
                f"{result['service']}"
            )

            print(
                f"  REQUIREMENTS : "
                f"{result['requirements']}"
            )

            print(
                f"  PROCEDURE    : "
                f"{result['procedure_candidates']}"
            )

            print(
                f"  TIME         : "
                f"{result['processing_time']}"
            )

            print(
                f"  OUTPUT       : "
                f"{result['outputs']}"
            )

            print(
                f"  LEGAL BASIS  : "
                f"{result['legal_basis']}"
            )


            if result["warnings"]:

                print(
                    "  WARNINGS:"
                )

                for warning in result[
                    "warnings"
                ]:

                    print(
                        f"    - {warning}"
                    )


        except Exception as exc:

            print(
                "  ERROR:"
                + str(exc)
            )

            results.append({

                "status":
                    "ENGINE_ERROR",

                "error":
                    str(exc),

                "file":
                    str(file)
            })


    manifest = {

        "engine":
            {
                "name":
                    "Nusantara SOP Semantic Reconstruction Engine",

                "version":
                    "2.0",

                "generated_at":
                    now()
            },

        "documents":
            results,

        "governance":
            {
                "production_db_modified":
                    False,

                "automatic_verification":
                    False,

                "human_validation_required":
                    True,

                "production_ingestion_allowed":
                    False
            }
    }


    manifest_path = (
        OUTPUT_ROOT
        / "semantic_manifest.json"
    )


    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


    print()
    print("=" * 78)
    print(
        "SEMANTIC RECONSTRUCTION COMPLETE"
    )
    print("=" * 78)

    print(
        f"TOTAL SOP : {len(results)}"
    )

    print(
        "READY      : "
        +
        str(
            sum(
                1
                for r in results
                if r.get(
                    "status"
                )
                ==
                "READY_FOR_HUMAN_VALIDATION"
            )
        )
    )

    print(
        "REVIEW     : "
        +
        str(
            sum(
                1
                for r in results
                if r.get(
                    "status"
                )
                ==
                "REVIEW_REQUIRED"
            )
        )
    )

    print()
    print(
        f"MANIFEST : {manifest_path}"
    )

    print()
    print(
        "Production DB : NOT TOUCHED"
    )

    print(
        "Verification   : HUMAN REQUIRED"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()
