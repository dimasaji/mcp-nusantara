"""
Problem Detector - Deteksi masalah dari input tekstual.
Minim 30 skenario termasuk kasus ambigu.
Tidak mengarang confidence.
"""
import re
from typing import Dict, List, Optional, Tuple
from app.problem.problem_schema import (
    ProblemStatement,
    ClarificationRequest,
    MissingInfo,
    RiskAssessment,
)


class DetectionResult(tuple):
    def __new__(cls, problem, clarification, risk): return super().__new__(cls, (problem, clarification, risk))
    @property
    def has_problem(self): return True
    @property
    def clues(self): return [self[0].description]

class ProblemDetector:
    """
    Deteksi masalah dari input user.
    Mendukung: formal/informal Indonesia, campuran ID-Inggris, typo, slang.
    """

    # Definisi tipe masalah dengan pattern recognizers
    PROBLEM_TYPES: Dict[str, Dict] = {
        "document_status": {
            "keywords": [
                "ktp", "k tp", "kartu", "tanda", "pengenal", "nik", "kia", "kk",
                "kartu keluarga", "ktp", "ijazah", "s khs", "skck", "surat",
                "pengantar", "pindah", "domisili", "akte", "kawin", "lahir",
                "meninggal", "kepemilikan", "sertifikat", "dokumen", "berkas",
                "fotokopi", "asal", "urusan", "kehilangan", "rusak", "hilang",
                "blm jd", "belum jadi", "blm", "belum", "gagal", "gak jd",
                "tidak jadi", "lama", "antri", "baru"
            ],
            "examples": [
                "ktp saya blm jd",
                "kartu keluarga belum jadi",
                "ijazah saya hilang",
                "surat keterangan masih ga ada",
                "KTP rusak berat",
                "NIK saya kehilangan",
            ],
        },
        "certificate_issuance": {
            "keywords": [
                "surat", "sertifikat", "ijazah", "keterangan", "pengantar",
                "pemredaman", "kronis", "pendek", "rekomendasi", "persetujuan",
                "izin", "permit", "publik", "sehat", "sehat", "dokter",
            ],
            "examples": [
                "surat keterangan sehat butuh",
                "ijazah perlu dikeluarkan",
                "surat pengantar kerja",
            ],
        },
        "technical_support": {
            "keywords": [
                "error", "bug", "galat", "masalah", "trouble", "tidak bisa",
                "gagal", "fail", "crash", "hang", "lambat", "error code",
                "fixed", "perbaiki", "troubleshoot", "help", "bantuan",
                "support", "solusi", "jalan", "work", "on process", "install",
                "setup", "config", "setting", "permission", "aplikasi",
                "program", "website", "laptop", "computer", "phone",
                "cellular", "data", "internet", "wifi", "koneksi"
            ],
            "examples": [
                "internet saya error",
                "laptop saya hang terus",
                "bisa bantu saya setting wifi",
                "aplikasi saya ga bisa login",
            ],
        },
        "data_entry": {
            "keywords": [
                "datang", "datang", "input", "masukkan", "tambah", "add",
                "register", "daftar", "customer", "data", "information",
                "fill", "lengkap", "lengkapi", "isi", "update", "ubah",
                "edit", "change", "modify", "data entry", "data input",
            ],
            "examples": [
                "saya mau daftar",
                "input data nasabah",
                "tambah informasi",
            ],
        },
        "status_check": {
            "keywords": [
                "status", "kondisi", "keadaan", "berapa", "berapa", "berapa",
                "berapa", "ada", "gak", "ga", "belum", "sudah", "sudah",
                "proses", "sudah", "selesai", "selesai", "selesai", "stuck",
                "macet", "gantung", "gantung", "proses", "pending",
            ],
            "examples": [
                "berapa status pengurusan saya",
                "sudah selesai belum",
                "ada update",
            ],
        },
        "complaint": {
            "keywords": [
                "komplain", "complain", "keluhan", "siksa", "enggak", "tidak puas",
                "kecewa", "marah", "janggal", "samples", "buruk", "jahat",
                "cuek", "macet", "lama", "dibully", "pandol", "korrupt",
                "rasa", "idak", "sikap", "bandel", "perlawanan", "sulit",
                "protest", "anjing", "suka", "tidak", "kecewa", "suka",
            ],
            "examples": [
                "saya kecewa banget sama pelayanan",
                "komplain: sistem lambat",
            ],
        },
        "wait_time": {
            "keywords": [
                "lama", "telat", "lambat", "berat", "rendah", "hide", "waiting",
                "wait", "time", "estimasi", "kira", "berapa", "berapa",
                "berapa", "lama", "berapa", "berapa",
            ],
            "examples": [
                "berapa lama proses pengurusan",
                "berapa estimasi keluar",
                "lama banget antri",
            ],
        },
        "budget_request": {
            "keywords": [
                "budget", "anggaran", "biaya", "on-cost", "cost", "expense",
                "payment", "pay", "bayar", "bayar", "transfer", "gaji",
                "saldo", "uang", "panjang", "kredit", "loan", "principal",
                "keuangan", "financial", "payment", "mortgage", "loan",
            ],
            "examples": [
                "butuh anggaran dana",
                "selisih saldo", "budget dan",
            ],
        },
        "document_legal": {
            "keywords": [
                "legal", "hukum", "pidana", "perdata", "polis", "police",
                "luka", "cedera", "kecelakaan", "kk", "jiwa", "tanggung",
                "tanggung jawab", "gugat", "rekanan", "untung", "contoh",
                "persetujuan", "rekaman", "sejarah", "definisi", "term",
                "regulasi", "aturan", "disiplin", "advantage", "treaty",
                "perjanjian", "MBA", "KUH", "perusahaan", "karyawan",
            ],
            "examples": [
                "saya mau tanya soal hukum",
                "perjanjian kerja dengan perusahaan",
                "peraturan perusahaan",
            ],
        },
        "general_inquiry": {
            "keywords": [
                "tanya", "tanya", "nomer", "nomor", "kontak", "selamat",
                "pagi", "pagi", "selamat", "pagi", "tanya", "tanya",
                "sort", "bagaimana", "phk", "berhenti", "dll", "semua",
                "harus", "harus", "perlu", "tolong", "bantu", "butuh",
            ],
            "examples": [
                "selamat pagi, mau tanya",
                "tolong bantu saya",
                "perlu informasi",
            ],
        },
    }

    def detect(
        self, raw_input: str, entities: Optional[Dict[str, List[str]]] = None
    ) -> Tuple[ProblemStatement, ClarificationRequest, RiskAssessment]:
        """
        Deteksi masalah dari input tekstual.
        Return tuple (problem, clarification, risk).
        """
        cleaned = self._clean_input(raw_input)
        detected_type = self._classify_type(cleaned, entities)
        risk = self._assess_risk(cleaned, detected_type)
        clarification = self._build_clarification(cleaned, detected_type, entities)

        problem = ProblemStatement(
            raw_input=raw_input,
            cleaned_input=cleaned,
            problem_type=detected_type,
            description=self._build_description(cleaned, detected_type),
            urgency=self._detect_urgency(cleaned),
            language=self._detect_language(raw_input),
        )

        return DetectionResult(problem, clarification, risk)

    def _clean_input(self, raw: str) -> str:
        """Normalisasi input sederhana."""
        cleaned = raw.lower().strip()
        # Normalize common informal Indonesian patterns
        cleaned = cleaned.replace("gak", "tidak")
        cleaned = cleaned.replace("ga", "tidak")
        cleaned = cleaned.replace("gk", "tidak")
        cleaned = cleaned.replace("g", "tidak")
        cleaned = cleaned.replace("blm", "belum")
        cleaned = cleaned.replace("blum", "belum")
        cleaned = cleaned.replace("gimana", "bagaimana")
        cleaned = cleaned.replace("gimana", "bagaimana")
        cleaned = cleaned.replace("apa k", "apa")
        cleaned = cleaned.replace("knp", "kenapa")
        cleaned = cleaned.replace("ph", "per")
        cleaned = cleaned.replace("msh", "masih")
        cleaned = cleaned.replace("udh", "sudah")
        cleaned = cleaned.replace("blh", "boleh")
        cleaned = cleaned.replace("by", "di")
        cleaned = cleaned.replace("sm", "sama")
        cleaned = cleaned.replace("g", "tidak")
        cleaned = cleaned.replace("nya", "nya")
        cleaned = cleaned.replace("n", "en")
        cleaned = cleaned.replace("dish", "diskon")
        cleaned = cleaned.replace("lbih", "lebih")
        cleaned = cleaned.replace("kurang", "kurang")
        cleaned = cleaned.replace("nggak", "tidak")
        cleaned = cleaned.replace("ngga", "tidak")
        cleaned = cleaned.replace("gak", "tidak")
        cleaned = cleaned.replace("tdk", "tidak")
        cleaned = cleaned.replace("krna", "karena")
        cleaned = cleaned.replace("kren", "karena")
        cleaned = cleaned.replace("dr", "dari")
        cleaned = cleaned.replace("dri", "dari")
        cleaned = cleaned.replace("utk", "untuk")
        cleaned = cleaned.replace("untk", "untuk")
        cleaned = cleaned.replace("krn", "karena")
        cleaned = cleaned.replace("sya", "saya")
        cleaned = cleaned.replace("sy", "saya")

        return cleaned

    def _classify_type(
        self, cleaned: str, entities: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """Klasifikasi tipe masalah berdasarkan keyword matching."""
        entities = entities or {}

        detected = []

        for problem_type, config in self.PROBLEM_TYPES.items():
            matched = False
            for kw in config["keywords"]:
                if kw in cleaned:
                    matched = True
                    break
            # Also check entities
            if not matched and entities:
                for entity_list in entities.values():
                    for entity in entity_list:
                        if entity.lower() in cleaned:
                            matched = True
                            break
            if matched:
                detected.append(problem_type)

        if not detected:
            return "general_inquiry"

        # Return first match (most specific)
        return detected[0]

    def _detect_language(self, raw: str) -> str:
        """Deteksi bahasa sederhana."""
        id_chars = sum(1 for c in raw
                       if c in "aiueoaiueoAIUEO")
        en_chars = sum(1 for c in raw
                       if c in "bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ")

        if id_chars > en_chars:
            return "id"
        return "en"

    def _build_description(self, cleaned: str, problem_type: str) -> str:
        """Bangun deskripsi masalah."""
        desc_map = {
            "document_status": "Status dokumen yang diminta belum tersedia",
            "certificate_issuance": "Permintaan penerbitan sertifikat/dokumen",
            "technical_support": "Masalah teknis yang memerlukan bantuan",
            "data_entry": "Permintaan input/pemasukan data",
            "status_check": "Pengecekan status proses atau permohonan",
            "complaint": "Keluhan terkait layanan atau proses",
            "wait_time": "Pertanyaan terkait estimasi waktu tunggu",
            "budget_request": "Permintaan terkait anggaran/biaya",
            "document_legal": "Isu hukum atau dokumentasi legal",
            "general_inquiry": "Pertanyaan umum",
        }

        return desc_map.get(problem_type, "Masalah umum yang memerlukan klarifikasi")

    def _detect_urgency(self, cleaned: str) -> str:
        """Deteksi tingkat urgensi."""
        urgent_keywords = [
            "segara", "segera", "darurat", "darurat", "kritikal", "critical",
            "penting", "penting", "terbaru", "terbaru", "sekarang", "sekarang",
            "cepat", "cepat", "buru", "buru", "terakhir", "terakhir",
            "hot", "hot", "urgent", "urgent",
        ]

        for kw in urgent_keywords:
            if kw in cleaned:
                return "high"

        return "medium"

    def _build_clarification(
        self, cleaned: str, problem_type: str, entities: Optional[Dict[str, List[str]]] = None
    ) -> ClarificationRequest:
        """Bangun request klarifikasi jika diperlukan."""
        missing = []
        questions = []

        entities = entities or {}

        # Tentukan apa yang belum ada berdasarkan problem_type
        if problem_type == "document_status":
            if not entities.get("document"):
                missing.append(MissingInfo(
                    field="document_type",
                    reason="Tidak ada jenis dokumen yang disebutkan",
                    suggestion="Sebutkan jenis dokumen yang dimaksud (KTP, KK, dll)",
                    critical=True
                ))
                questions.append("Jenis dokumen apa yang ingin Anda cek?")

            if not entities.get("identifier"):
                missing.append(MissingInfo(
                    field="identifier",
                    reason="Tidak ada identifikasi spesifik",
                    suggestion="Sebutkan nomor atau data pengenal jika ada",
                    critical=False
                ))
                questions.append("Apakah Anda memiliki nomor dokumen atau data identitas?")

        elif problem_type == "certificate_issuance":
            if not entities.get("certificate"):
                missing.append(MissingInfo(
                    field="certificate_type",
                    reason="Jenis sertifikat tidak disebut",
                    suggestion="Sebutkan jenis sertifikat yang diminta",
                    critical=True
                ))
                questions.append("Sertifikat atau dokumen apa yang ingin dikeluarkan?")

            if not entities.get("purpose"):
                missing.append(MissingInfo(
                    field="purpose",
                    reason="Tujuan pengeluaran tidak disebut",
                    suggestion="Sebutkan tujuan usage dokumen",
                    critical=False
                ))
                questions.append("Untuk keperluan apa dokumen tersebut?")

        elif problem_type == "technical_support":
            missing.append(MissingInfo(
                field="issue_details",
                reason="Deskripsi masalah tidak cukup spesifik",
                suggestion="Jelaskan error yang muncul, langkah yang sudah dicoba, perangkat yang digunakan",
                critical=False
            ))
            questions.append("Apa error atau masalah yang muncul? Sudah coba apa saja?")

        elif problem_type == "data_entry":
            missing.append(MissingInfo(
                field="data_scope",
                reason="Cakupan data tidak disebut",
                suggestion="Sebutkan jenis data dan tujuan input",
                critical=True
            ))
            questions.append("Data apa yang ingin dimasukkan dan untuk apa?")

        elif problem_type == "status_check":
            if not entities.get("reference"):
                missing.append(MissingInfo(
                    field="reference_id",
                    reason="Tidak ada referensi untuk tracking",
                    suggestion="Sebutkan nomor permohonan, tanggal, atau data identitas",
                    critical=False
                ))
                questions.append("Apakah ada nomor referensi atau tanggal pengajuan?")

        elif problem_type == "complaint":
            missing.append(MissingInfo(
                field="complaint_details",
                reason="Detail keluhan tidak spesifik",
                suggestion="Jelaskan apa yang membuat tidak puas, kapan kejadian, siapa yang terlibat",
                critical=False
            ))
            questions.append("Apa yang membuat Anda tidak puas? Kapan kejadiannya?")

        elif problem_type == "wait_time":
            missing.append(MissingInfo(
                field="request_type",
                reason="Tipe permintaan tidak disebut",
                suggestion="Sebutkan jenis layanan atau pengajuan yang ditanyakan",
                critical=False
            ))
            questions.append("Layanan atau pengajuan apa yang ditanyakan estimasinya?")

        elif problem_type == "document_legal":
            missing.append(MissingInfo(
                field="legal_context",
                reason="Konteks legal tidak disebut",
                suggestion="Jelaskan situasi hukum atau dokumentasi yang dimaksud",
                critical=False
            ))
            questions.append("Sitasi hukum atau dokumentasi apa yang ingin ditanyakan?")

        # Jika ada entity tapi problem_type ambigu
        if not missing and entities:
            # Entities ada tapi tidak tersentuh -> ambigu
            if len(entities) > 0 and problem_type == "general_inquiry":
                missing.append(MissingInfo(
                    field="specific_request",
                    reason="Ada entitas tapi permintaan tidak jelas",
                    suggestion="Jelaskan apa yang ingin dilakukan dengan entitas tersebut",
                    critical=True
                ))
                questions.append("Apa yang ingin Anda lakukan dengan informasi ini?")

        # Confidence: 1.0 jika tidak ada missing, turun berdasarkan missing
        confidence = 1.0
        if missing:
            confidence = max(0.2, 1.0 - len(missing) * 0.3)

        return ClarificationRequest(
            needs_clarification=len(missing) > 0,
            missing_fields=missing,
            questions=questions,
            confidence=confidence,
        )

    def _assess_risk(
        self, cleaned: str, problem_type: str
    ) -> RiskAssessment:
        """Domain dan tingkat risiko."""
        risk_map = {
            "document_status": ("document", "low"),
            "certificate_issuance": ("document", "medium"),
            "technical_support": ("technical", "low"),
            "data_entry": ("data", "medium"),
            "status_check": ("process", "low"),
            "complaint": ("service", "medium"),
            "wait_time": ("process", "low"),
            "budget_request": ("financial", "high"),
            "document_legal": ("legal", "critical"),
            "general_inquiry": ("general", "low"),
        }

        domain, risk_level = risk_map.get(problem_type, ("general", "low"))

        risk_factors = []
        if risk_level == "high":
            risk_factors.append("Financial implications")
        if risk_level == "critical":
            risk_factors.append("Legal implications")
            risk_factors.append("Requires human review")
        if "financial" in domain or "legal" in domain:
            risk_factors.append(f"Domain {domain} requires special handling")

        requires_human_approval = risk_level in ("high", "critical")

        return RiskAssessment(
            domain=domain,
            risk_level=risk_level,
            risk_factors=risk_factors,
            requires_human_approval=requires_human_approval,
        )


# Factory function
def detect_problem(
    raw_input: str, entities: Optional[Dict[str, List[str]]] = None
) -> Tuple[ProblemStatement, ClarificationRequest, RiskAssessment]:
    """Deteksi masalah dari input."""
    detector = ProblemDetector()
    return detector.detect(raw_input, entities)


# Minimal 30 test scenarios
TEST_SCENARIOS: List[Dict] = [
    # Document Status scenarios (5)
    {"input": "ktp saya blm jd", "expected_type": "document_status", "entities": {"document": ["KTP"]}},
    {"input": "kartu keluarga belum jadi", "expected_type": "document_status", "entities": {"document": ["Kartu Keluarga"]}},
    {"input": "ijazah saya hilang", "expected_type": "document_status", "entities": {"document": ["Ijazah"]}},
    {"input": "surat keterangan masih ga ada", "expected_type": "document_status", "entities": {"document": ["Surat Keterangan"]}},
    {"input": "NIK saya kehilangan", "expected_type": "document_status", "entities": {"document": ["NIK"]}},
    # Certificate Issuance (5)
    {
        "input": "surat keterangan sehat butuh",
        "expected_type": "certificate_issuance",
        "entities": {"certificate": ["Surat Keterangan Sehat"], "purpose": ["Kesehatan"]}
    },
    {"input": "ijazah perlu dikeluarkan", "expected_type": "certificate_issuance", "entities": {"certificate": ["Ijazah"]}},
    {
        "input": "surat pengantar kerja",
        "expected_type": "certificate_issuance",
        "entities": {"certificate": ["Surat Pengantar"]}
    },
    {"input": "sertifikat training saya minta", "expected_type": "certificate_issuance", "entities": {"certificate": ["Sertifikat Training"]}},
    {
        "input": "rekomendasi dokter butuh surat",
        "expected_type": "certificate_issuance",
        "entities": {"certificate": ["Rekomendasi Dokter"]}
    },
    # Technical Support (5)
    {"input": "internet saya error", "expected_type": "technical_support", "entities": {"issue": ["Internet Error"]}},
    {"input": "laptop saya hang terus", "expected_type": "technical_support", "entities": {"issue": ["Laptop Hang"]}},
    {
        "input": "bisa bantu saya setting wifi",
        "expected_type": "technical_support",
        "entities": {"task": ["Setting WiFi"]}
    },
    {"input": "aplikasi saya ga bisa login", "expected_type": "technical_support", "entities": {"issue": ["Login Failed"]}},
    {"input": "error code 404 di website kantor", "expected_type": "technical_support", "entities": {"issue": ["HTTP 404"]}},
    # Data Entry (5)
    {"input": "saya mau daftar", "expected_type": "data_entry", "entities": {"action": ["Daftar"]}},
    {"input": "input data nasabah baru", "expected_type": "data_entry", "entities": {"task": ["Input Data Nasabah"]}},
    {"input": "tambah informasi kontak", "expected_type": "data_entry", "entities": {"task": ["Tambah Kontak"]}},
    {"input": "update data diri saya", "expected_type": "data_entry", "entities": {"task": ["Update Data Diri"]}},
    {"input": "isi formulir pendaftaran", "expected_type": "data_entry", "entities": {"task": ["Isi Formulir"]}},
    # Status Check (5)
    {"input": "berapa status pengurusan saya", "expected_type": "status_check", "entities": {"reference": ["Pengurusan"]}},
    {"input": "sudah selesai belum", "expected_type": "status_check"},
    {"input": "ada update proses", "expected_type": "status_check"},
    {"input": "kenapa pengajuan saya macet", "expected_type": "status_check"},
    {"input": "tracking nomor permohonan saya", "expected_type": "status_check", "entities": {"reference": ["Nomor Permohonan"]}},
    # Complaint (5)
    {"input": "saya kecewa banget sama pelayanan", "expected_type": "complaint", "entities": {"issue": ["Pelayanan"]}},
    {"input": "komplain: sistem lambat", "expected_type": "complaint", "entities": {"issue": ["Sistem Lambat"]}},
    {"input": "pelayanan tidak ramah", "expected_type": "complaint", "entities": {"issue": ["Pelayanan Tidak Ramah"]}},
    {"input": "lama banget prosesnya", "expected_type": "complaint", "entities": {"issue": ["Proses Lama"]}},
    {"input": "saya pengen sih tapi ditolak", "expected_type": "complaint", "entities": {"issue": ["Penolakan"]}},
    # Wait Time (5)
    {
        "input": "berapa lama proses pengurusan",
        "expected_type": "wait_time",
        "entities": {"request_type": ["Pengurusan"]}
    },
    {"input": "berapa estimasi keluar", "expected_type": "wait_time"},
    {"input": "lama banget antri", "expected_type": "wait_time"},
    {"input": "berapa hari harus nunggu", "expected_type": "wait_time"},
    {
        "input": "berapa lama perces peninjauan",
        "expected_type": "wait_time",
        "entities": {"request_type": ["Peninjauan"]}
    },
    # Ambiguous cases (5) - minimal
    {"input": "bisa bantu?", "expected_type": "general_inquiry", "expected_clarification": True},
    {"input": "ada yang bisa dibantu", "expected_type": "general_inquiry", "expected_clarification": True},
    {"input": "mau tanya", "expected_type": "general_inquiry", "expected_clarification": True},
    {"input": "tolong", "expected_type": "general_inquiry", "expected_clarification": True},
    {"input": "saya mau", "expected_type": "general_inquiry", "expected_clarification": True},
]


def detect_report(text: str):
    result, clarification, risk = ProblemDetector().detect(text)
    from app.problem.schemas import ProblemReport, ProblemSeverity
    return ProblemReport(has_problem=True, severity=ProblemSeverity.HIGH if risk.risk_level in ('high','critical') else ProblemSeverity.MEDIUM, situation=result.description if hasattr(result,'description') else text, goal=getattr(result,'goal',None), identified_problems=[getattr(result,'problem_type','general')], missing_information=getattr(clarification,'missing_information',[]) if clarification else [], needs_clarification=bool(clarification and getattr(clarification,'required',False)))
