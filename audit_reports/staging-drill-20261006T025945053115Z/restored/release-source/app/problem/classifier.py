"""
Problem Classifier - Klasifikasi masalah ke kategori dan subkategori.
"""
from typing import Dict, List, Optional, Tuple
from app.problem.problem_schema import ProblemStatement


class ProblemClassifier:
    """
    Klasifikasi masalah berdasarkan deskripsi.
    Mendukung multi-kategori dan subkategori.
    """

    # Kategori utama dan subkategori
    CATEGORIES: Dict[str, Dict[str, List[str]]] = {
        "data_document": {
            "subcategories": ["document_status", "certificate_issuance", "data_entry", "document_legal"],
            "keywords": [
                "ktp", "kk", "k tp", "kartu", "nik", "kia", "ijazah",
                "surat", "pengantar", "sertifikat", "dokumen", "berkas",
                "data", "input", "register", "daftar", "formulir", "form",
                "legal", "hukum", "peraturan", "rekomendasi", "permohonan",
            ],
        },
        "technical_technical": {
            "subcategories": ["technical_support", "wait_time"],
            "keywords": [
                "error", "bug", "galat", "masalah", "trouble", "tidak bisa",
                "gagal", "fail", "crash", "hang", "lambat", "error code",
                "fixed", "perbaiki", "troubleshoot", "help", "bantuan",
                "support", "solusi", "jalan", "work", "on process", "install",
                "setup", "config", "setting", "permission", "aplikasi",
                "program", "website", "laptop", "computer", "phone",
                "cellular", "data", "internet", "wifi", "koneksi",
                "berlangsung", "proses", "lama", "antri", "waiting",
            ],
        },
        "process": {
            "subcategories": ["status_check", "complaint", "budget_request"],
            "keywords": [
                "status", "kepuasan", "komplain", "complain", "keluhan",
                "siksa", "negatif", "kecewa", "marah", "janggal", "buruk",
                "cuek", "macet", "lama", "dibully", "pandol",
                "budget", "anggaran", "biaya", "on-cost", "cost", "expense",
                "payment", "pay", "bayar", "bayar", "transfer", "gaji",
                "saldo", "uang", "panjang", "kredit", "loan", "principal",
                "keuangan", "financial", "payment", "mortgage", "loan",
                "proses", "pengurusan", "pending", "approve", "verification",
            ],
        },
        "general": {
            "subcategories": ["general_inquiry"],
            "keywords": [
                "tanya", "tanya", "nomer", "nomor", "kontak", "selamat",
                "pagi", "pagi", "selamat", "pagi", "tanya", "tanya",
                "sort", "bagaimana", "phk", "berhenti", "dll", "semua",
                "harus", "harus", "perlu", "tolong", "bantu", "butuh",
                "info", "informasi", "pengetahuan", "question", "answer",
            ],
        },
    }

    def __init__(self):
        self._category_scores: Dict[str, Dict[str, float]] = {}

    def classify(
        self,
        problem: ProblemStatement,
    ) -> Tuple[str, List[str], float]:
        """
        Klasifikasi masalah ke kategori utama dan subkategori.
        Return (primary_category, all_matched_subcategories, confidence).
        """
        cleaned = problem.cleaned_input.lower()

        scores = {}
        for category, config in self.CATEGORIES.items():
            score = self._compute_category_score(cleaned, config)
            scores[category] = {"score": score, "subcategories": config["subcategories"]}

        # Sort by score
        sorted_categories = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

        # Primary category = highest score
        primary_category = sorted_categories[0][0] if sorted_categories else "general"

        # Get all subcategories from primary category
        subcategories = scores[primary_category]["subcategories"]

        # Confidence = max score (if > 0) else 0.5 default
        max_score = scores[primary_category]["score"] if scores else 0
        confidence = min(1.0, max_score) if max_score > 0 else 0.5

        return primary_category, subcategories, confidence

    def _compute_category_score(self, cleaned: str, config: Dict) -> float:
        """Hitung score untuk kategori berdasarkan keyword match."""
        score = 0.0
        matched_keywords = []

        for keyword in config["subcategories"]:
            if keyword in cleaned:
                score += 1.0
                matched_keywords.append(keyword)

        # Bonus untuk keyword tambahan
        for keyword in config["subcategories"]:
            if keyword in cleaned:
                matched_keywords.append(keyword)

        return score

    def classify_with_subcategory(
        self,
        problem: ProblemStatement,
    ) -> Dict[str, any]:
        """
        Klasifikasi lengkap dengan subkategori.
        Return dict dengan primary_category, subcategories, confidence, dan detail.
        """
        primary, subcategories, confidence = self.classify(problem)

        # Detail per subcategory
        subcategory_details = []
        for subcat in subcategories:
            detail = {
                "subcategory": subcat,
                "matched": subcat in problem.cleaned_input.lower(),
                "confidence": confidence,
            }
            subcategory_details.append(detail)

        # Tambahkan detail klasifikasi ke problem
        problem.classifications = [
            {
                "primary_category": primary,
                "subcategories": subcategories,
                "confidence": confidence,
                "raw_input": problem.cleaned_input,
            }
        ]

        return {
            "primary_category": primary,
            "subcategories": subcategories,
            "confidence": confidence,
            "details": subcategory_details,
        }


def classify_problem(problem: ProblemStatement) -> Dict[str, any]:
    """Klasifikasi masalah."""
    classifier = ProblemClassifier()
    return classifier.classify_with_subcategory(problem)
