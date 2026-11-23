from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import requests


ROOT = Path(r"C:\Users\dmaza\mcp-starter")

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

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llama3.2:1b"

VERSION = "3.0"


# ============================================================
# UTIL
# ============================================================

def clean(value: Any) -> str:

    if value is None:
        return ""

    text = str(value)

    text = text.replace("\x00", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def unique(items):

    result = []

    seen = set()

    for item in items:

        item = clean(item)

        if not item:
            continue

        key = item.lower()

        if key not in seen:

            seen.add(key)

            result.append(item)

    return result


# ============================================================
# DISCOVERY
# ============================================================

def discover():

    return sorted(
        INPUT_ROOT.glob(
            "*/structured/sop_structured.json"
        )
    )


# ============================================================
# EVIDENCE
# ============================================================

class EvidenceAdapter:

    def __init__(
        self,
        document: dict
    ):

        self.document = document

        self.pages = (
            document.get("pages")
            or []
        )

        self.items = []

        self.build()


    def build(self):

        for page in self.pages:

            page_no = page.get(
                "page"
            )

            text = clean(
                page.get("text")
            )

            confidence = float(
                page.get(
                    "average_confidence",
                    0
                )
                or 0
            )

            if text:

                self.items.append({

                    "id":
                        f"P{page_no}-TEXT",

                    "page":
                        page_no,

                    "type":
                        "page_text",

                    "text":
                        text,

                    "confidence":
                        confidence,
                })


            words = (
                page.get("words")
                or []
            )

            groups = {}

            for word in words:

                word_text = clean(
                    word.get("text")
                )

                if not word_text:
                    continue

                key = (
                    word.get("block_num"),
                    word.get("par_num"),
                    word.get("line_num"),
                )

                groups.setdefault(
                    key,
                    []
                ).append(
                    word
                )


            line_number = 0

            for group in groups.values():

                group = sorted(
                    group,
                    key=lambda x:
                        float(
                            x.get(
                                "left",
                                0
                            )
                            or 0
                        )
                )

                line_text = " ".join(
                    clean(
                        x.get("text")
                    )
                    for x in group
                    if clean(
                        x.get("text")
                    )
                )

                if not line_text:
                    continue

                line_number += 1

                conf = [
                    float(
                        x.get(
                            "confidence",
                            0
                        )
                        or 0
                    )
                    for x in group
                ]

                avg = (
                    sum(conf)
                    / len(conf)
                    if conf
                    else 0
                )

                bbox = {

                    "left":
                        min(
                            int(
                                x.get(
                                    "left",
                                    0
                                )
                                or 0
                            )
                            for x in group
                        ),

                    "top":
                        min(
                            int(
                                x.get(
                                    "top",
                                    0
                                )
                                or 0
                            )
                            for x in group
                        ),

                    "right":
                        max(
                            int(
                                x.get(
                                    "right",
                                    0
                                )
                                or 0
                            )
                            for x in group
                        ),

                    "bottom":
                        max(
                            int(
                                x.get(
                                    "bottom",
                                    0
                                )
                                or 0
                            )
                            for x in group
                        ),
                }

                self.items.append({

                    "id":
                        f"P{page_no}-L{line_number}",

                    "page":
                        page_no,

                    "type":
                        "ocr_line",

                    "text":
                        line_text,

                    "confidence":
                        round(
                            avg,
                            2
                        ),

                    "bbox":
                        bbox,
                })


    def all_text(self):

        return "\n".join(
            x["text"]
            for x in self.items
            if x["type"]
            == "page_text"
        )


    def relevant(
        self,
        keywords,
        limit=12
    ):

        scored = []

        for item in self.items:

            text = item["text"].lower()

            score = sum(
                1
                for keyword in keywords
                if keyword.lower()
                in text
            )

            if score > 0:

                scored.append(
                    (
                        score,
                        item
                    )
                )


        scored.sort(
            key=lambda x:
                (
                    x[0],
                    x[1].get(
                        "confidence",
                        0
                    )
                ),
            reverse=True
        )

        return [
            item
            for _, item in scored[:limit]
        ]


# ============================================================
# METADATA EXTRACTION
# ============================================================

def extract_from_text(
    text: str,
    patterns
):

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

            if value:
                return value

    return None


def extract_metadata(
    document: dict,
    evidence: EvidenceAdapter
):

    identity = (
        document.get("identity")
        or {}
    )

    classification = (
        document.get("classification")
        or {}
    )

    full_text = evidence.all_text()

    # --------------------------------------------------------
    # SOP NUMBER
    # --------------------------------------------------------

    sop_number = (
        identity.get(
            "sop_number"
        )
        or extract_from_text(
            full_text,
            [
                r"NO\s*SOP\s*[:\-]\s*([A-Z0-9./_-]+)",
                r"NO\s*SOP\s+([A-Z0-9./_-]+)",
            ]
        )
    )


    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = (
        identity.get(
            "title"
        )
        or extract_from_text(
            full_text,
            [
                r"NAMA\s*SOP\s*[:\-]\s*(.+?)(?:\s+LEGAL|$)",
                r"NAMA\s*SOP\s*[:\-]\s*(.+)",
            ]
        )
    )


    # remove obvious OCR garbage
    if title:

        title = clean(title)

        title = re.split(
            r"\s+(?:LEGAL|DASAR|KETERKAITAN|PERALATAN|PERLENGKAPAN)\b",
            title,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0]

        if len(title) > 250:
            title = title[:250]


    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    effective_date = (
        identity.get(
            "effective_date"
        )
        or extract_from_text(
            full_text,
            [
                r"TGL\s*TERBIT\s*[:\-]\s*([A-Z0-9 ./-]+)",
            ]
        )
    )


    # --------------------------------------------------------
    # SERVICE
    # --------------------------------------------------------

    service = (
        classification.get(
            "service"
        )
    )

    if not service:

        title_lower = (
            (title or "")
            .lower()
        )

        service_map = [

            (
                [
                    "akta kelahiran",
                    "kelahiran"
                ],
                "akta_kelahiran"
            ),

            (
                [
                    "akta kematian",
                    "kematian"
                ],
                "akta_kematian"
            ),

            (
                [
                    "ktp-el",
                    "ktp el",
                    "ktpel"
                ],
                "ktp_el"
            ),

            (
                [
                    "kartu keluarga",
                    "kk"
                ],
                "kartu_keluarga"
            ),

            (
                [
                    "kia"
                ],
                "kia"
            ),

            (
                [
                    "data pribadi"
                ],
                "data_pribadi"
            ),

            (
                [
                    "informasi data penduduk"
                ],
                "informasi_data_penduduk"
            ),
        ]

        for terms, value in service_map:

            if any(
                term in title_lower
                for term in terms
            ):

                service = value

                break


    # --------------------------------------------------------
    # CHANNEL
    # --------------------------------------------------------

    channel = (
        classification.get(
            "channel"
        )
        or []
    )

    if not channel:

        text_lower = full_text.lower()

        if "online" in text_lower:

            channel.append(
                "online"
            )

        if (
            "rumah sakit" in text_lower
            or "klinik" in text_lower
            or "bidan" in text_lower
        ):

            channel.append(
                "rumah_sakit_klinik_bidan"
            )


    return {

        "sop_number":
            sop_number,

        "title":
            title,

        "effective_date":
            effective_date,

        "service":
            service,

        "channel":
            unique(channel),

        "applicant":
            unique(
                classification.get(
                    "applicant"
                )
                or []
            ),
    }


# ============================================================
# DETERMINISTIC DATA
# ============================================================

def get_list(
    document,
    key
):

    value = document.get(key)

    if not isinstance(
        value,
        list
    ):
        return []

    return unique(value)


# ============================================================
# OLLAMA
# ============================================================

def call_ollama(
    prompt
):

    payload = {

        "model":
            MODEL,

        "prompt":
            prompt,

        "stream":
            False,

        "format":
            "json",

        "options": {

            "temperature":
                0,

            "num_ctx":
                4096,

            "num_predict":
                900,
        },
    }

    started = time.time()

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=90
        )

        elapsed = round(
            time.time()
            - started,
            2
        )

        if response.status_code != 200:

            return {

                "ok":
                    False,

                "error":
                    f"HTTP {response.status_code}",

                "elapsed":
                    elapsed,
            }


        body = response.json()

        raw = body.get(
            "response",
            ""
        )

        if not raw:

            return {

                "ok":
                    False,

                "error":
                    "EMPTY_RESPONSE",

                "elapsed":
                    elapsed,
            }


        try:

            parsed = json.loads(
                raw
            )

        except Exception:

            match = re.search(
                r"\{.*\}",
                raw,
                re.DOTALL
            )

            if not match:

                return {

                    "ok":
                        False,

                    "error":
                        "INVALID_JSON",

                    "elapsed":
                        elapsed,
                }

            parsed = json.loads(
                match.group(0)
            )


        return {

            "ok":
                True,

            "data":
                parsed,

            "elapsed":
                elapsed,
        }


    except requests.Timeout:

        return {

            "ok":
                False,

            "error":
                "OLLAMA_TIMEOUT",

            "elapsed":
                90,
        }


    except Exception as exc:

        return {

            "ok":
                False,

            "error":
                str(exc),
        }


# ============================================================
# SEMANTIC SECTION
# ============================================================

def semantic_section(
    section,
    evidence_items,
    metadata
):

    evidence_text = "\n".join(

        f"[{x['id']}] "
        f"{x['text']}"

        for x in evidence_items
    )

    prompt = f"""
Anda adalah semantic engine untuk SOP pemerintah.

Gunakan HANYA evidence.

Jangan mengarang.

SERVICE:
{metadata.get('service')}

TITLE:
{metadata.get('title')}

SECTION:
{section}

EVIDENCE:
{evidence_text}

Tugas:
identifikasi makna section secara ringkas.

Output JSON:

{{
  "items": [
    {{
      "text": "",
      "evidence": []
    }}
  ]
}}

Setiap item WAJIB memiliki evidence ID
yang benar-benar terdapat pada input.

Jika tidak ada informasi yang dapat dipastikan:
items = [].

JSON SAJA.
"""

    return call_ollama(
        prompt
    )


# ============================================================
# SEMANTIC PROCESS
# ============================================================

def run_semantic(
    document,
    evidence,
    metadata
):

    sections = {

        "requirements": [
            "persyaratan",
            "berkas",
            "kelengkapan",
            "ktp",
            "kartu keluarga",
            "buku nikah",
            "dokumen",
        ],

        "procedure": [
            "mengisi",
            "memeriksa",
            "memproses",
            "menginput",
            "mengajukan",
            "memverifikasi",
            "mencetak",
            "menerima",
            "mengambil",
            "sertifikasi elektronik",
        ],

        "risk": [
            "risiko",
            "terselip",
            "offline",
            "rusak",
            "tertunda",
            "lambat",
        ],
    }

    result = {}

    llm_errors = []

    for section, keywords in sections.items():

        items = evidence.relevant(
            keywords,
            limit=12
        )

        if not items:

            result[section] = []

            continue


        response = semantic_section(
            section,
            items,
            metadata
        )

        if not response.get(
            "ok"
        ):

            llm_errors.append({

                "section":
                    section,

                "error":
                    response.get(
                        "error"
                    ),
            })

            result[section] = []

            continue


        section_data = (
            response.get(
                "data"
            )
            or {}
        )

        section_items = (
            section_data.get(
                "items"
            )
            or []
        )

        clean_items = []

        valid_ids = {
            x["id"]
            for x in evidence.items
        }

        for item in section_items:

            if not isinstance(
                item,
                dict
            ):
                continue

            text = clean(
                item.get("text")
            )

            refs = [
                ref
                for ref in (
                    item.get(
                        "evidence"
                    )
                    or []
                )
                if ref in valid_ids
            ]

            if text and refs:

                clean_items.append({

                    "text":
                        text,

                    "evidence":
                        refs,
                })


        result[section] = clean_items


    return result, llm_errors


# ============================================================
# QUALITY
# ============================================================

def quality_gate(
    metadata,
    evidence,
    semantic,
    llm_errors
):

    warnings = []

    if not metadata.get(
        "sop_number"
    ):

        warnings.append(
            "SOP_NUMBER_MISSING"
        )


    if not metadata.get(
        "title"
    ):

        warnings.append(
            "TITLE_MISSING"
        )


    if not metadata.get(
        "service"
    ):

        warnings.append(
            "SERVICE_MISSING"
        )


    if not evidence.items:

        warnings.append(
            "EVIDENCE_EMPTY"
        )


    if llm_errors:

        warnings.append(
            "SEMANTIC_LLM_PARTIAL_FAILURE"
        )


    total_semantic = sum(
        len(
            semantic.get(
                key,
                []
            )
        )
        for key in [
            "requirements",
            "procedure",
            "risk",
        ]
    )


    if total_semantic == 0:

        warnings.append(
            "SEMANTIC_RESULT_EMPTY"
        )


    return {

        "status":
            "REVIEW_REQUIRED"
            if warnings
            else
            "READY_FOR_HUMAN_VALIDATION",

        "warnings":
            unique(warnings),

        "evidence_count":
            len(evidence.items),

        "semantic_items":
            total_semantic,

        "llm_partial_errors":
            llm_errors,

        "automatic_verification":
            False,

        "human_validation_required":
            True,
    }


# ============================================================
# PROCESS
# ============================================================

def process(
    file
):

    document = json.loads(
        file.read_text(
            encoding="utf-8"
        )
    )

    evidence = EvidenceAdapter(
        document
    )

    metadata = extract_metadata(
        document,
        evidence
    )

    print(
        f"\n[{file.parent.parent.name}]"
    )

    print(
        "  SOP NUMBER :",
        metadata["sop_number"]
    )

    print(
        "  TITLE      :",
        metadata["title"]
    )

    print(
        "  SERVICE    :",
        metadata["service"]
    )

    print(
        "  PAGES      :",
        len(evidence.pages)
    )

    print(
        "  EVIDENCE   :",
        len(evidence.items)
    )


    semantic, llm_errors = run_semantic(
        document,
        evidence,
        metadata
    )


    deterministic = {

        "processing_time":
            get_list(
                document,
                "processing_time"
            ),

        "outputs":
            get_list(
                document,
                "outputs"
            ),

        "legal_basis":
            get_list(
                document,
                "legal_basis"
            ),

        "requirements_source":
            get_list(
                document,
                "requirements"
            ),

        "procedure_source":
            document.get(
                "procedure"
            )
            if isinstance(
                document.get(
                    "procedure"
                ),
                list
            )
            else [],
    }


    gate = quality_gate(
        metadata,
        evidence,
        semantic,
        llm_errors
    )


    output = {

        "schema_version":
            "3.0",

        "engine": {

            "name":
                "Nusantara Master Semantic Understanding Engine",

            "version":
                VERSION,

            "model":
                MODEL,
        },

        "source":
            document.get(
                "source",
                {}
            ),

        "identity":
            metadata,

        "semantic":
            semantic,

        "deterministic":
            deterministic,

        "evidence": {

            "pages":
                len(evidence.pages),

            "items":
                len(evidence.items),

            "types": {

                "page_text":
                    sum(
                        1
                        for x in evidence.items
                        if x["type"]
                        == "page_text"
                    ),

                "ocr_line":
                    sum(
                        1
                        for x in evidence.items
                        if x["type"]
                        == "ocr_line"
                    ),
            },
        },

        "llm": {

            "partial_errors":
                llm_errors,

            "model":
                MODEL,
        },

        "quality_gate":
            gate,

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
                True,
        },
    }


    output_dir = (
        OUTPUT_ROOT
        / file.parent.parent.name
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir
        / "semantic_understanding.json"
    )

    output_file.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


    print(
        "  SEMANTIC    :",
        sum(
            len(semantic.get(k, []))
            for k in semantic
        )
    )

    print(
        "  LLM ERRORS  :",
        len(llm_errors)
    )

    print(
        "  STATUS      :",
        gate["status"]
    )

    print(
        "  OUTPUT      :",
        output_file
    )


    return output


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)

    print(
        "NUSANTARA MASTER SEMANTIC UNDERSTANDING ENGINE"
    )

    print(
        "VERSION :",
        VERSION
    )

    print(
        "MODEL   :",
        MODEL
    )

    print("=" * 72)


    files = discover()

    print(
        "STRUCTURED SOP :",
        len(files)
    )


    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )


    manifest = []


    for index, file in enumerate(
        files,
        1
    ):

        print(
            f"\n[{index}/{len(files)}]"
        )

        try:

            output = process(
                file
            )

            manifest.append({

                "file":
                    str(file),

                "sop_number":
                    output["identity"][
                        "sop_number"
                    ],

                "title":
                    output["identity"][
                        "title"
                    ],

                "service":
                    output["identity"][
                        "service"
                    ],

                "evidence":
                    output["evidence"][
                        "items"
                    ],

                "status":
                    output["quality_gate"][
                        "status"
                    ],
            })

        except Exception as exc:

            print(
                "  ENGINE ERROR :",
                exc
            )

            manifest.append({

                "file":
                    str(file),

                "status":
                    "ENGINE_ERROR",

                "error":
                    str(exc),
            })


    manifest_file = (
        OUTPUT_ROOT
        / "semantic_manifest.json"
    )

    manifest_file.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


    print("\n" + "=" * 72)

    print(
        "SEMANTIC ENGINE V3 COMPLETE"
    )

    print(
        "TOTAL :",
        len(files)
    )

    print(
        "MANIFEST :",
        manifest_file
    )

    print("=" * 72)

    print(
        "Original PDF       : NOT MODIFIED"
    )

    print(
        "OCR Evidence       : NOT MODIFIED"
    )

    print(
        "Production DB      : NOT TOUCHED"
    )

    print(
        "Automatic Verify   : DISABLED"
    )

    print(
        "Human Validation   : REQUIRED"
    )


if __name__ == "__main__":

    main()
