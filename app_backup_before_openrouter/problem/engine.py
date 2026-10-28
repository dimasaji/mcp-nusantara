"""
Problem Engine - Orchestrasi deteksi, klasifikasi, resolusi masalah.
Pipeline: human story → situation → problem → goal → constraints → missing info → possible solution.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from app.problem.problem_schema import (
    ProblemStatement,
    Goal,
    ClarificationRequest,
    RiskAssessment,
    MissingInfo,
    PossibleSolution,
    ProblemResolution,
    ProblemSchema,
)
from app.problem.detector import ProblemDetector, detect_problem
from app.problem.classifier import ProblemClassifier, classify_problem


logger = logging.getLogger(__name__)


class ProblemEngine:
    """
    Engine untuk memproses masalah manusia.
    Input: ProblemSchema (dengan raw_input, language, detected_intent, entities)
    Output: ProblemResolution lengkap.
    """

    def __init__(
        self,
        detector: Optional[ProblemDetector] = None,
        classifier: Optional[ProblemClassifier] = None,
    ):
        self.detector = ProblemDetector()
        self._detector = detector or ProblemDetector()
        self._classifier = classifier or ProblemClassifier()
    def resolve(
        self,
        schema: ProblemSchema,
    ) -> ProblemResolution:
        """
        Proses masalah dari awal sampai resolusi.
        """
        logger.info(f"Memproses masalah: {schema.raw_input[:50]}...")

        # 1. Deteksi masalah
        problem, clarification, risk = self._detector.detect(
            schema.raw_input, schema.entities or None
        )

        # 2. Klasifikasi
        classification = self._classifier.classify_with_subcategory(problem)

        # 3. Bangun goal
        goal = self._infer_goal(problem, classification, schema.entities)

        # 4. Bangun missing info
        missing_info, clarification_request = self._build_missing(
            problem, clarification, goal, schema.entities
        )

        # 5. Cek apakah perlu klarifikasi
        if clarification_request.needs_clarification and risk.risk_level != "critical":
            # Return dengan clarification request
            resolution = ProblemResolution(
                problem_id=generate_problem_id(),
                original_input=schema.raw_input,
                language=problem.language,
                problem=problem,
                goal=goal,
                risk=risk,
                missing_info=missing_info,
                clarification_request=clarification_request,
                resolution_status="needs_clarification",
            )
            return resolution

        # 6. Generate solusi
        solutions = self._generate_solutions(
            problem, goal, risk, missing_info, classification
        )

        # 7. Select solusi (jika ada)
        selected = self._select_solution(solutions, risk) if solutions else None

        # 8. Build resolusi
        resolution = ProblemResolution(
            problem_id=generate_problem_id(),
            original_input=schema.raw_input,
            language=problem.language,
            problem=problem,
            goal=goal,
            constraints_applied=self._build_constraints(goal, risk),
            risk=risk,
            missing_info=missing_info,
            clarification_request=None,
            possible_solutions=solutions,
            selected_solution=selected,
            resolution_status="solved" if selected else "in_progress",
        )

        return resolution

    def _infer_goal(
        self,
        problem: ProblemStatement,
        classification: Dict[str, any],
        entities: Optional[Dict[str, List[str]]] = None,
    ) -> Goal:
        """Infer goal dari masalah."""
        goal_text = self._generate_goal_text(problem.problem_type, entities)

        return Goal(
            description=goal_text,
            outcome=self._generate_outcome(problem.problem_type),
            constraints=self._generate_constraints(problem.problem_type, risk=None),
            success_criteria=self._generate_success_criteria(problem.problem_type),
        )

    def _generate_goal_text(
        self,
        problem_type: str,
        entities: Optional[Dict[str, List[str]]] = None,
    ) -> str:
        """Generate text goal."""
        goal_map = {
            "document_status": "Mendapatkan informasi status dokumen yang diminta",
            "certificate_issuance": "Mendapatkan dokumen/sertifikat yang diminta",
            "technical_support": "Memecahkan masalah teknis yang dilaporkan",
            "data_entry": "Memasukkan/memperbarui data yang diminta",
            "status_check": "Mengetahui status terkini dari permohonan/proses",
            "complaint": "Menangani keluhan yang disampaikan",
            "wait_time": "Mengetahui estimasi waktu proses",
            "budget_request": "Memproses permintaan anggaran/biaya",
            "document_legal": "Memberikan informasi/masukan terkait isu legal",
            "general_inquiry": "Menjawab pertanyaan umum",
        }

        return goal_map.get(problem_type, "Memahami dan membantu menyelesaikan masalah")

    def _generate_outcome(self, problem_type: str) -> Optional[str]:
        """Generate outcome yang diharapkan."""
        outcome_map = {
            "document_status": "Informasi status tersedia",
            "certificate_issuance": "Dokumen diterbitkan",
            "technical_support": "Masalah terpecahkan",
            "data_entry": "Data berhasil dimasukkan/diperbarui",
            "status_check": "Status terverifikasi",
            "complaint": "Keluhan tertangani",
            "wait_time": "Estimasi waktu diberikan",
            "budget_request": "Permintaan anggaran diproses",
            "document_legal": "Informasi legal diberikan",
            "general_inquiry": "Pertanyaan terjawab",
        }

        return outcome_map.get(problem_type)

    def _generate_constraints(
        self,
        problem_type: str,
        risk: Optional[RiskAssessment] = None,
    ) -> List[str]:
        """Generate constraints berdasarkan problem type."""
        constraints = []

        base_constraints = {
            "document_status": ["Harus ada identitas pemohon", "Dokumen harus valid"],
            "certificate_issuance": ["Harus ada persyaratan yang terpenuhi", "Dokumen asli harus tersedia"],
            "technical_support": ["Perlu akses ke sistem/perangkat", "Harus detail error"],
            "data_entry": ["Data harus lengkap dan benar", "Harus ada konfirmasi"],
            "status_check": ["Harus ada referensi permohonan", "Harus ada akses ke sistem"],
            "complaint": ["Harus ada detail kejadian", "Harus ada pihak yang terlibat"],
            "wait_time": ["Harus ada jenis layanan yang dimaksud"],
            "budget_request": ["Harus ada rincian anggaran", "Harus ada persetujuan manajer"],
            "document_legal": ["Harus ada konsultasi dengan ahli hukum", "Harus ada dokumen pendukung"],
            "general_inquiry": ["Tidak ada constraint khusus"],
        }

        constraints.extend(base_constraints.get(problem_type, ["Tidak ada constraint khusus"]))

        if risk and risk.risk_level == "critical":
            constraints.append("Harus melalui human approval")
        if risk and risk.risk_level == "high":
            constraints.append("Perlu verifikasi tambahan")

        return constraints

    def _generate_success_criteria(
        self,
        problem_type: str,
    ) -> List[str]:
        """Generate success criteria."""
        return [
            f"Masalah {problem_type} berhasil diidentifikasi",
            f"Tujuan '{self._generate_goal_text(problem_type, None)}' tercapai",
            "Tidak ada informasi yang tertinggal",
        ]

    def _build_missing(
        self,
        problem: ProblemStatement,
        clarification: ClarificationRequest,
        goal: Goal,
        entities: Optional[Dict[str, List[str]]] = None,
    ) -> Tuple[List[MissingInfo], ClarificationRequest]:
        """Bangun missing information dari clarification."""
        missing = list(clarification.missing_fields)
        questions = list(clarification.questions)

        # Tambahkan missing dari goal jika ada
        if goal and not goal.outcome:
            missing.append(MissingInfo(
                field="outcome",
                reason="Outcome yang diinginkan tidak disebutkan",
                suggestion="Sebutkan apa yang diharapkan setelah proses selesai",
                critical=False
            ))
            questions.append("Apa yang Anda harapkan setelah proses ini selesai?")

        return missing, ClarificationRequest(
            needs_clarification=len(missing) > 0,
            missing_fields=missing,
            questions=questions,
            confidence=clarification.confidence,
        )

    def _generate_solutions(
        self,
        problem: ProblemStatement,
        goal: Goal,
        risk: RiskAssessment,
        missing: List[MissingInfo],
        classification: Dict[str, any],
    ) -> List[PossibleSolution]:
        """Generate possible solutions."""
        solutions = []

        problem_type = problem.problem_type
        has_missing = len(missing) > 0

        # Template solusi per tipe masalah
        solution_templates = {
            "document_status": [
                {
                    "approach": "Cek status dokumen melalui sistem",
                    "steps": [
                        "Verifikasi identitas pemohon",
                        "Cari dokumen berdasarkan identitas",
                        "Periksa status terkini",
                        "Berikan informasi status",
                    ],
                    "pros": ["Cepat", "Akurat", "Terintegrasi"],
                    "cons": ["Tidak tahu jika sistem down"],
                    "estimated_effort": "low",
                    "confidence": 0.85,
                    "requires_clarification_before": has_missing,
                },
                {
                    "approach": "Hubungi pihak terkait jika sistem tidak tersedia",
                    "steps": [
                        "Identifikasi pihak yang memegang dokumen",
                        "Hubungi via telepon/email",
                        "Minta informasi status",
                        "Laporkan ke user",
                    ],
                    "pros": ["Bisa jika sistem down", "Personal"],
                    "cons": ["Lebih lambat", "Tergantung ketersediaan pihak"],
                    "estimated_effort": "medium",
                    "confidence": 0.6,
                    "requires_clarification_before": has_missing,
                },
            ],
            "certificate_issuance": [
                {
                    "approach": "Proses penerbitan dokumen melalui sistem",
                    "steps": [
                        "Cek kelengkapan persyaratan",
                        "Proses permohonan",
                        "Verifikasi data",
                        "Terbitkan dokumen",
                        "Berikan ke user",
                    ],
                    "pros": ["Standar", "Terkelola"],
                    "cons": ["Perlu verifikasi manual untuk beberapa dokumen"],
                    "estimated_effort": "medium",
                    "confidence": 0.8,
                    "requires_clarification_before": has_missing,
                },
                {
                    "approach": "Tunda jika persyaratan belum lengkap",
                    "steps": [
                        "Identifikasi persyaratan yang kurang",
                        "Informasi ke user",
                        "Tunggu persyaratan lengkap",
                        "Lanjutkan proses",
                    ],
                    "pros": ["Tidak ada kelengkapan", "User tahu apa yang kurang"],
                    "cons": ["Delayed", "User harus submit lagi"],
                    "estimated_effort": "low",
                    "confidence": 0.7,
                    "requires_clarification_before": True,
                },
            ],
            "technical_support": [
                {
                    "approach": "Troubleshooting sistematis",
                    "steps": [
                        "Kumpulkan info error detail",
                        "Cek logs/system status",
                        "Identifikasi root cause",
                        "Terapkan solusi",
                        "Verifikasi penyelesaian",
                    ],
                    "pros": ["Systematis", "Bisa diulang"],
                    "cons": ["Perlu waktu", "Perlu akses teknis"],
                    "estimated_effort": "medium",
                    "confidence": 0.75,
                    "requires_clarification_before": has_missing,
                },
                {
                    "approach": "Escalasi ke tim teknis jika perlu",
                    "steps": [
                        "Kumpulkan info untuk escalation",
                        "Kirim ke tim teknis",
                        "Follow-up",
                        "Laporkan ke user",
                    ],
                    "pros": ["Pakai ahli", "Lebih mungkin solve"],
                    "cons": ["Waiting time", "Biaya escalation"],
                    "estimated_effort": "high",
                    "confidence": 0.5,
                    "requires_clarification_before": False,
                },
            ],
            "data_entry": [
                {
                    "approach": "Input data melalui form/system",
                    "steps": [
                        "Validasi data masukan",
                        "Check duplikat",
                        "Simpan data",
                        "Konfirmasi ke user",
                    ],
                    "pros": ["Cepat", "Terintegrasi", "Tercatat"],
                    "cons": ["Perlu validasi manual jika data ambigu"],
                    "estimated_effort": "low",
                    "confidence": 0.9,
                    "requires_clarification_before": has_missing,
                },
                {
                    "approach": "Manual entry jika system tidak tersedia",
                    "steps": [
                        "Siapkan form manual",
                        "Input data",
                        "Verifikasi",
                        "Update system nanti",
                    ],
                    "pros": ["Bisa dilakukan", "Fleksibel"],
                    "cons": ["Rawan error", "Butuh re-entry nanti"],
                    "estimated_effort": "medium",
                    "confidence": 0.6,
                    "requires_clarification_before": False,
                },
            ],
            "status_check": [
                {
                    "approach": "Cek status melalui sistem",
                    "steps": [
                        "Identifikasi referensi/status",
                        "Query sistem",
                        "Ambil status terkini",
                        "Berikan informasi",
                    ],
                    "pros": ["Cepat", "Akurat"],
                    "cons": ["Sistem harus tersedia"],
                    "estimated_effort": "low",
                    "confidence": 0.9,
                    "requires_clarification_before": has_missing,
                },
                {
                    "approach": "Konfirmasi dengan pihak berwenang",
                    "steps": [
                        "Hubungi pihak yang memegang status",
                        "Minta konfirmasi",
                        "Laporkan ke user",
                    ],
                    "pros": ["Akurat dari sumber resmi"],
                    "cons": ["Lebih lambat"],
                    "estimated_effort": "medium",
                    "confidence": 0.65,
                    "requires_clarification_before": has_missing,
                },
            ],
            "complaint": [
                {
                    "approach": "Proses penanganan keluhan",
                    "steps": [
                        "Dokumentasi keluhan",
                        "Kategorikan tingkat keparahan",
                        "Assign ke penanggung jawab",
                        "Kelola dan follow-up",
                        "Berikan feedback ke user",
                    ],
                    "pros": ["Terkendali", "Ada record"],
                    "cons": ["Perlu koordinasi", "Bisa lambat"],
                    "estimated_effort": "medium",
                    "confidence": 0.7,
                    "requires_clarification_before": has_missing,
                },
                {
                    "approach": "Immediate resolution jika memungkinkan",
                    "steps": [
                        "Cek apakah bisa selesaikan sekarang",
                        "Jika ya, selesaikan",
                        "Kalau tidak, jelaskan alasan",
                        "Tawarkan alternatif",
                    ],
                    "pros": ["Fast jika bisa", "User puas"],
                    "cons": ["Tidak semua keluhan bisa selesai instan"],
                    "estimated_effort": "low",
                    "confidence": 0.5,
                    "requires_clarification_before": True,
                },
            ],
            "wait_time": [
                {
                    "approach": "Hitung estimasi waktu berdasarkan historical data",
                    "steps": [
                        "Kategorikan jenis layanan",
                        "Cek historical average",
                        "Hitung estimasi",
                        "Berikan range waktu",
                    ],
                    "pros": ["Data-driven", "Realistis"],
                    "cons": ["Perlu historical data", "Bisa berubah"],
                    "estimated_effort": "low",
                    "confidence": 0.8,
                    "requires_clarification_before": has_missing,
                },
                {
                    "approach": "Tanyakan ke tim terkait untuk estimasi lebih akurat",
                    "steps": [
                        "Hubungi tim operasional",
                        "Minta estimasi",
                        "Laporkan ke user",
                    ],
                    "pros": ["Lebih akurat"],
                    "cons": ["Lebih lambat", "Tergantung ketersediaan tim"],
                    "estimated_effort": "medium",
                    "confidence": 0.6,
                    "requires_clarification_before": False,
                },
            ],
            "budget_request": [
                {
                    "approach": "Proses permintaan anggaran",
                    "steps": [
                        "Verifikasi detail permintaan",
                        "Cek ketersediaan anggaran",
                        "Submit ke approval",
                        "Konfirmasi hasil",
                    ],
                    "pros": ["Terproses formal", "Ada audit trail"],
                    "cons": ["Perlu approval", "Bisa lama"],
                    "estimated_effort": "high",
                    "confidence": 0.7,
                    "requires_clarification_before": True,
                },
            ],
            "document_legal": [
                {
                    "approach": "Rujuk ke ahli hukum untuk konsultasi",
                    "steps": [
                        "Dokumentasi isu legal",
                        "Rujuk ke tim hukum / ahli",
                        "Dapatkan opini/konsultasi",
                        "Berikan informasi ke user",
                    ],
                    "pros": ["Akurat legally", "Tanggung jawab jelas"],
                    "cons": ["Butuh ahli", "Bisa lambat"],
                    "estimated_effort": "high",
                    "confidence": 0.6,
                    "requires_clarification_before": True,
                },
            ],
            "general_inquiry": [
                {
                    "approach": "Jawab berdasarkan pengetahuan umum",
                    "steps": [
                        "Pahami pertanyaan",
                        "Cari jawaban dari knowledge base",
                        "Jika tidak ada, tanyakan klarifikasi",
                        "Berikan jawaban",
                    ],
                    "pros": ["Cepat untuk pertanyaan umum"],
                    "cons": ["Tidak specific jika kurang info"],
                    "estimated_effort": "low",
                    "confidence": 0.7,
                    "requires_clarification_before": has_missing,
                },
            ],
        }

        templates = solution_templates.get(problem_type, solution_templates["general_inquiry"])

        for tpl in templates:
            solutions.append(PossibleSolution(
                approach=tpl["approach"],
                steps=tpl["steps"],
                pros=tpl["pros"],
                cons=tpl["cons"],
                estimated_effort=tpl["estimated_effort"],
                confidence=tpl["confidence"],
                requires_clarification_before=tpl["requires_clarification_before"],
            ))

        # Sort by confidence descending
        solutions.sort(key=lambda x: x.confidence, reverse=True)

        return solutions

    def _select_solution(
        self,
        solutions: List[PossibleSolution],
        risk: RiskAssessment,
    ) -> Optional[PossibleSolution]:
        """Select solusi terbaik berdasarkan risk dan confidence."""
        if not solutions:
            return None

        # Jika high risk, butuh human approval -> pilih yang tidak butuh clarification
        if risk.requires_human_approval:
            # Cari solusi yang bisa dijalankan tanpa clarification
            for sol in solutions:
                if not sol.requires_clarification_before:
                    sol.approach = f"[HUMAN APPROVAL REQUIRED] {sol.approach}"
                    return sol
            # Kalau semua butuh clarification, return solusi tertinggi tapi dengan catatan
            return solutions[0]

        # Pilih solusi dengan confidence tertinggi yang tidak butuh clarification
        # atau kalau tidak ada, pilih tertinggi secara umum
        for sol in solutions:
            if not sol.requires_clarification_before:
                return sol

        # Kalau semua butuh clarification, return yang confidence tertinggi
        return solutions[0]

    def _build_constraints(
        self,
        goal: Goal,
        risk: RiskAssessment,
    ) -> List[str]:
        """Bangun constraints dari goal dan risk."""
        constraints = list(goal.constraints) if goal else []

        if risk and risk.risk_level in ("high", "critical"):
            constraints.append("Memerlukan human approval untuk eksekusi")

        return constraints


def generate_problem_id() -> str:
    """Generate ID unik untuk masalah."""
    import uuid
    return f"PRB-{uuid.uuid4().hex[:8].upper()}"


def process_problem(schema: ProblemSchema) -> ProblemResolution:
    """Process masalah dari schema."""
    engine = ProblemEngine()
    return engine.resolve(schema)

# Compatibility API for Phase 5 tests and API Gateway.
def _compat_analyze(self, user_input: str, context=None):
    result, clarification, risk = self._detector.detect(user_input) if hasattr(self, '_detector') else ProblemDetector().detect(user_input)
    from app.problem.schemas import ProblemReport, ProblemSeverity
    missing = []
    if clarification is not None:
        missing = getattr(clarification, 'missing_information', []) or []
    return ProblemReport(
        has_problem=True,
        severity=ProblemSeverity.CRITICAL if risk.risk_level == 'critical' else ProblemSeverity.HIGH if risk.risk_level == 'high' else ProblemSeverity.MEDIUM,
        situation=user_input,
        goal=getattr(result, 'goal', None) or 'Menyelesaikan kebutuhan pengguna',
        identified_problems=[getattr(result, 'problem_type', None) or getattr(result, 'description', None) or 'general'],
        missing_information=missing,
        needs_clarification=bool(missing),
    )
try:
    ProblemEngine.analyze = _compat_analyze
except NameError:
    pass
