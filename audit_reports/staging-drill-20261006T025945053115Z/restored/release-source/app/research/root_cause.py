from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Iterable


class RootCauseAnalysisError(ValueError):
    """Raised when root-cause analysis input is invalid."""


@dataclass(frozen=True)
class RootCauseCandidate:
    cause: str
    evidence_ids: tuple[str, ...]
    confidence: float
    rationale: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "cause": self.cause,
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class RootCauseResult:
    analysis_id: str
    gap_id: str
    component: str
    candidates: tuple[RootCauseCandidate, ...]
    selected_cause: str | None
    evidence_count: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "gap_id": self.gap_id,
            "component": self.component,
            "candidates": [
                candidate.to_payload()
                for candidate in self.candidates
            ],
            "selected_cause": self.selected_cause,
            "evidence_count": self.evidence_count,
        }


class RootCauseAnalyzer:
    """
    NUSANTARA GATE 17.3
    Evidence-bound deterministic root-cause analysis.

    Prinsip:
    - evidence wajib tersedia
    - setiap candidate harus memiliki evidence
    - confidence harus berada pada 0.0 - 1.0
    - tidak menggunakan LLM
    - tidak melakukan write / patch / execute
    - analysis_id deterministic
    - tidak memutuskan perubahan production
    """

    def analyze(
        self,
        *,
        gap_id: str,
        component: str,
        evidence: Iterable[dict[str, Any]],
        candidates: Iterable[dict[str, Any]],
    ) -> RootCauseResult:
        gap_id = str(gap_id).strip()
        component = str(component).strip()

        if not gap_id:
            raise RootCauseAnalysisError(
                "gap_id wajib diisi"
            )

        if not component:
            raise RootCauseAnalysisError(
                "component wajib diisi"
            )

        normalized_evidence = self._normalize_evidence(
            evidence
        )

        if not normalized_evidence:
            raise RootCauseAnalysisError(
                "Root cause membutuhkan evidence"
            )

        evidence_ids = {
            item["evidence_id"]
            for item in normalized_evidence
        }

        normalized_candidates = self._normalize_candidates(
            candidates,
            evidence_ids,
        )

        if not normalized_candidates:
            raise RootCauseAnalysisError(
                "Minimal satu root-cause candidate wajib ada"
            )

        canonical = {
            "gap_id": gap_id,
            "component": component,
            "evidence": normalized_evidence,
            "candidates": [
                candidate.to_payload()
                for candidate in normalized_candidates
            ],
        }

        serialized = json.dumps(
            canonical,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )

        analysis_id = (
            "RCA-"
            + hashlib.sha256(
                serialized.encode("utf-8")
            ).hexdigest()[:12].upper()
        )

        selected = self._select_candidate(
            normalized_candidates
        )

        return RootCauseResult(
            analysis_id=analysis_id,
            gap_id=gap_id,
            component=component,
            candidates=tuple(normalized_candidates),
            selected_cause=selected,
            evidence_count=len(normalized_evidence),
        )

    @staticmethod
    def _normalize_evidence(
        evidence: Iterable[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if evidence is None:
            return []

        normalized: list[dict[str, Any]] = []

        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                raise RootCauseAnalysisError(
                    f"Evidence #{index + 1} harus dictionary"
                )

            raw_id = item.get("evidence_id")

            if raw_id is None:
                source = str(
                    item.get("source", "")
                ).strip()

                evidence_type = str(
                    item.get("evidence_type", "")
                ).strip()

                data = item.get("data", {})

                if not source or not evidence_type:
                    raise RootCauseAnalysisError(
                        "Evidence harus memiliki evidence_id "
                        "atau source + evidence_type"
                    )

                identity = {
                    "source": source,
                    "evidence_type": evidence_type,
                    "data": data,
                }

                raw_id = (
                    "EVD-"
                    + hashlib.sha256(
                        json.dumps(
                            identity,
                            sort_keys=True,
                            ensure_ascii=False,
                            default=str,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest()[:12].upper()
                )

            evidence_id = str(raw_id).strip()

            if not evidence_id:
                raise RootCauseAnalysisError(
                    "evidence_id tidak boleh kosong"
                )

            normalized_item = {
                "evidence_id": evidence_id,
                "source": str(
                    item.get("source", "")
                ).strip().lower(),
                "evidence_type": str(
                    item.get("evidence_type", "")
                ).strip().lower(),
                "data": item.get("data", {}),
            }

            if not normalized_item["source"]:
                raise RootCauseAnalysisError(
                    f"Evidence {evidence_id} "
                    "tidak memiliki source"
                )

            if not normalized_item["evidence_type"]:
                raise RootCauseAnalysisError(
                    f"Evidence {evidence_id} "
                    "tidak memiliki evidence_type"
                )

            if not isinstance(
                normalized_item["data"],
                dict,
            ):
                raise RootCauseAnalysisError(
                    f"Evidence {evidence_id} "
                    "data harus dictionary"
                )

            normalized.append(normalized_item)

        normalized.sort(
            key=lambda item: item["evidence_id"]
        )

        ids = [
            item["evidence_id"]
            for item in normalized
        ]

        if len(ids) != len(set(ids)):
            raise RootCauseAnalysisError(
                "Duplicate evidence_id ditemukan"
            )

        return normalized

    @classmethod
    def _normalize_candidates(
        cls,
        candidates: Iterable[dict[str, Any]],
        valid_evidence_ids: set[str],
    ) -> list[RootCauseCandidate]:
        if candidates is None:
            return []

        normalized: list[RootCauseCandidate] = []

        for index, item in enumerate(candidates):
            if not isinstance(item, dict):
                raise RootCauseAnalysisError(
                    f"Candidate #{index + 1} harus dictionary"
                )

            cause = str(
                item.get("cause", "")
            ).strip()

            rationale = str(
                item.get("rationale", "")
            ).strip()

            raw_ids = item.get("evidence_ids", [])

            if not cause:
                raise RootCauseAnalysisError(
                    "Candidate cause wajib diisi"
                )

            if not rationale:
                raise RootCauseAnalysisError(
                    f"Rationale kosong untuk cause: {cause}"
                )

            if not isinstance(raw_ids, (list, tuple)):
                raise RootCauseAnalysisError(
                    f"evidence_ids harus list untuk: {cause}"
                )

            evidence_ids = tuple(
                sorted(
                    {
                        str(value).strip()
                        for value in raw_ids
                        if str(value).strip()
                    }
                )
            )

            if not evidence_ids:
                raise RootCauseAnalysisError(
                    f"Cause tanpa evidence: {cause}"
                )

            unknown = (
                set(evidence_ids)
                - valid_evidence_ids
            )

            if unknown:
                raise RootCauseAnalysisError(
                    f"Evidence tidak ditemukan untuk "
                    f"{cause}: {sorted(unknown)}"
                )

            try:
                confidence = float(
                    item.get("confidence")
                )
            except (TypeError, ValueError):
                raise RootCauseAnalysisError(
                    f"Confidence tidak valid untuk: {cause}"
                )

            if not 0.0 <= confidence <= 1.0:
                raise RootCauseAnalysisError(
                    f"Confidence di luar 0..1 untuk: {cause}"
                )

            normalized.append(
                RootCauseCandidate(
                    cause=cause,
                    evidence_ids=evidence_ids,
                    confidence=confidence,
                    rationale=rationale,
                )
            )

        normalized.sort(
            key=lambda candidate: (
                -candidate.confidence,
                candidate.cause,
                candidate.evidence_ids,
            )
        )

        duplicate_causes = [
            candidate.cause
            for candidate in normalized
        ]

        if len(duplicate_causes) != len(
            set(duplicate_causes)
        ):
            raise RootCauseAnalysisError(
                "Duplicate root-cause ditemukan"
            )

        return normalized

    @staticmethod
    def _select_candidate(
        candidates: list[RootCauseCandidate],
    ) -> str | None:
        if not candidates:
            return None

        highest = candidates[0]

        # Hanya memilih jika confidence memenuhi
        # ambang deterministik.
        if highest.confidence < 0.50:
            return None

        return highest.cause
