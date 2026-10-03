from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class EvidenceCollectionError(ValueError):
    pass


class EvidenceCollector:
    """
    Gate 17.2 - deterministic evidence normalization.

    Evidence Collector hanya mengumpulkan dan menormalisasi
    evidence yang diberikan oleh subsystem.

    Tidak:
    - memanggil LLM
    - melakukan write
    - melakukan patch
    - menjalankan command
    - mengubah production
    """

    ALLOWED_SOURCES = {
        "runtime",
        "test",
        "regression",
        "graph",
        "rag",
        "evaluation",
        "audit",
        "static",
        "user_feedback",
    }

    def collect(
        self,
        *,
        source: str,
        evidence_type: str,
        data: dict,
    ) -> dict:
        source = str(source).strip().lower()
        evidence_type = str(evidence_type).strip().lower()

        if source not in self.ALLOWED_SOURCES:
            raise EvidenceCollectionError(
                f"Evidence source tidak valid: {source}"
            )

        if not evidence_type:
            raise EvidenceCollectionError(
                "evidence_type wajib diisi"
            )

        if not isinstance(data, dict):
            raise EvidenceCollectionError(
                "Evidence data harus berupa dictionary"
            )

        if not data:
            raise EvidenceCollectionError(
                "Evidence data tidak boleh kosong"
            )

        normalized = {
            "source": source,
            "evidence_type": evidence_type,
            "data": self._normalize(data),
        }

        return normalized

    def collect_many(
        self,
        items: list[dict],
    ) -> list[dict]:
        if not isinstance(items, list):
            raise EvidenceCollectionError(
                "items harus berupa list"
            )

        result = []

        for item in items:
            if not isinstance(item, dict):
                raise EvidenceCollectionError(
                    "Setiap evidence harus dictionary"
                )

            result.append(
                self.collect(
                    source=item.get("source", ""),
                    evidence_type=item.get(
                        "evidence_type", ""
                    ),
                    data=item.get("data", {}),
                )
            )

        result.sort(
            key=lambda item: (
                item["source"],
                item["evidence_type"],
                repr(item["data"]),
            )
        )

        return result

    @classmethod
    def _normalize(cls, value):
        if isinstance(value, dict):
            return {
                str(key): cls._normalize(value[key])
                for key in sorted(value, key=str)
            }

        if isinstance(value, (list, tuple)):
            return [
                cls._normalize(item)
                for item in value
            ]

        if isinstance(value, (str, int, float, bool)) or value is None:
            return value

        return str(value)
