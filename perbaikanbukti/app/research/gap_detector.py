from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Iterable


GAP_TYPES = {
    "test_failure",
    "regression",
    "runtime_error",
    "quality",
    "performance",
    "grounding",
    "retrieval",
    "architecture",
    "coverage",
    "consistency",
    "unknown",
}

SEVERITIES = {"low", "medium", "high", "critical"}


class GapDetectionError(ValueError):
    pass


@dataclass(frozen=True)
class Gap:
    gap_id: str
    component: str
    gap_type: str
    description: str
    severity: str
    evidence: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "component": self.component,
            "gap_type": self.gap_type,
            "description": self.description,
            "severity": self.severity,
            "evidence": [dict(item) for item in self.evidence],
        }


class GapDetector:
    """
    Gate 17.1 - deterministic gap detection.

    Prinsip:
    - evidence wajib ada
    - tidak menggunakan LLM
    - tidak melakukan write/patch/execute
    - gap_id deterministik
    - evidence menjadi dasar gap
    """

    def detect(
        self,
        *,
        component: str,
        gap_type: str,
        description: str,
        severity: str,
        evidence: Iterable[dict[str, Any]],
    ) -> Gap:
        component = str(component).strip()
        gap_type = str(gap_type).strip().lower()
        description = str(description).strip()
        severity = str(severity).strip().lower()

        if not component:
            raise GapDetectionError("component wajib diisi")

        if gap_type not in GAP_TYPES:
            raise GapDetectionError(f"gap_type tidak valid: {gap_type}")

        if not description:
            raise GapDetectionError("description wajib diisi")

        if severity not in SEVERITIES:
            raise GapDetectionError(f"severity tidak valid: {severity}")

        normalized_evidence = self._normalize_evidence(evidence)

        if not normalized_evidence:
            raise GapDetectionError(
                "Gap wajib memiliki evidence"
            )

        payload = {
            "component": component,
            "gap_type": gap_type,
            "description": description,
            "severity": severity,
            "evidence": normalized_evidence,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )

        gap_id = "GAP-" + hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()[:12].upper()

        return Gap(
            gap_id=gap_id,
            component=component,
            gap_type=gap_type,
            description=description,
            severity=severity,
            evidence=tuple(normalized_evidence),
        )

    @staticmethod
    def _normalize_evidence(
        evidence: Iterable[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if evidence is None:
            return []

        normalized: list[dict[str, Any]] = []

        for item in evidence:
            if not isinstance(item, dict):
                raise GapDetectionError(
                    "Setiap evidence harus berupa dictionary"
                )

            clean = {
                str(key): value
                for key, value in item.items()
            }

            if not clean:
                raise GapDetectionError(
                    "Evidence tidak boleh kosong"
                )

            normalized.append(clean)

        normalized.sort(
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            )
        )

        return normalized
