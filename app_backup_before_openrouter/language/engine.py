"""
Language Engine - Pipeline utama.
raw input → normalization → language detection → intent → entity → structured understanding.
"""
from typing import Optional, Dict, List
from app.language.schemas import (
    NormalizationResult,
    LanguageDetectionResult,
    IntentResult,
    EntityResult,
    StructuredUnderstanding,
    PipelineConfig,
    PipelineResult,
)
from app.language.normalizer import TextNormalizer
from app.language.intent import IntentClassifier
from app.language.entity import EntityExtractor


class LanguageEngine:
    """
    Language Engine - orchestrator pipeline NLP.
    """

    def __init__(
        self,
        normalizer: Optional[TextNormalizer] = None,
        intent_classifier: Optional[IntentClassifier] = None,
        entity_extractor: Optional[EntityExtractor] = None,
        config: Optional[PipelineConfig] = None,
    ):
        self._normalizer = normalizer or TextNormalizer()
        self._intent_classifier = intent_classifier or IntentClassifier()
        self._entity_extractor = entity_extractor or EntityExtractor()
        self._config = config or PipelineConfig()

    def process(
        self,
        text: str,
        config: Optional[PipelineConfig] = None,
    ) -> PipelineResult:
        """
        Jalankan pipeline lengkap: raw input → structured understanding.
        """
        pipeline_config = config or self._config
        steps = []
        result = None

        # Step 1: Normalization (jika diaktifkan)
        if pipeline_config.normalize:
            norm_result = self._normalizer.normalize(text)
            steps.append("normalization")
            text_to_process = norm_result.normalized
        else:
            norm_result = NormalizationResult(
                original=text,
                normalized=text,
                changes=[],
            )
            text_to_process = text
            steps.append("skip_normalization")

        # Step 2: Language Detection
        if pipeline_config.detect_language:
            lang_result = self._detect_language(text_to_process)
            steps.append("language_detection")
        else:
            lang_result = LanguageDetectionResult(
                language="id",
                confidence=0.5,
                is_mixed=False,
                languages={},
            )
            steps.append("skip_language_detection")

        # Step 3: Intent Classification
        if pipeline_config.detect_intent:
            intent_result = self._intent_classifier.classify(text_to_process)
            steps.append("intent_classification")
        else:
            intent_result = IntentResult(
                intent="unknown",
                confidence=0.0,
                category=None,
                parent_intent=None,
            )
            steps.append("skip_intent")

        # Step 4: Entity Extraction
        if pipeline_config.extract_entities:
            entity_result = self._entity_extractor.extract(text_to_process)
            steps.append("entity_extraction")
        else:
            entity_result = EntityResult(
                entities={},
                confidence=0.0,
                raw_matches=[],
            )
            steps.append("skip_entity_extraction")

        # Build structured understanding
        result = StructuredUnderstanding(
            text=text_to_process,
            language=lang_result,
            intent=intent_result,
            entities=entity_result,
            metadata={
                "original_text": text,
                "normalization_changes": norm_result.changes,
                "pipeline_steps": steps,
            },
        )

        return PipelineResult(
            input=text,
            output=result,
            steps=steps,
            duration_ms=0,
        )

    def _detect_language(self, text: str) -> LanguageDetectionResult:
        """Deteksi bahasa ringan untuk chat; memprioritaskan indikator Bahasa Indonesia."""
        import re

        tokens = re.findall(r"[a-zA-Z]+", text.lower())
        if not tokens:
            return LanguageDetectionResult(language="id", confidence=0.1, is_mixed=False, languages={})

        id_words = {
            "saya", "aku", "kamu", "anda", "yang", "dan", "atau", "untuk", "dengan",
            "dari", "ke", "di", "ini", "itu", "belum", "sudah", "mau", "bisa", "tidak",
            "tolong", "cara", "bagaimana", "apa", "cek", "ktp", "kk", "nik", "dokumen",
        }
        en_words = {
            "the", "is", "are", "how", "what", "where", "when", "why", "please", "help",
            "document", "status", "check", "can", "could", "my", "your", "not", "yet",
        }
        id_hits = sum(t in id_words for t in tokens)
        en_hits = sum(t in en_words for t in tokens)
        id_ratio = id_hits / len(tokens)
        en_ratio = en_hits / len(tokens)
        if id_hits == 0 and en_hits == 0:
            return LanguageDetectionResult(language="id", confidence=0.5, is_mixed=False, languages={"id": 0.5, "en": 0.5})
        mixed = id_hits > 0 and en_hits > 0
        language = "id" if id_hits >= en_hits else "en"
        confidence = max(id_ratio, en_ratio) * (0.9 if mixed else 1.0)
        return LanguageDetectionResult(
            language=language, confidence=round(confidence, 3), is_mixed=mixed,
            languages={"id": round(id_ratio, 3), "en": round(en_ratio, 3)},
        )

    def get_structured_understanding(self, text: str) -> StructuredUnderstanding:
        """Shortcut: proses dan return structured understanding saja."""
        result = self.process(text)
        return result.output

    def extract_intent(self, text: str) -> IntentResult:
        """Extract intent saja."""
        norm = self._normalizer.normalize(text)
        lang = self._detect_language(norm.normalized)
        return self._intent_classifier.classify(norm.normalized)

    def extract_entities(self, text: str) -> EntityResult:
        """Extract entity saja."""
        norm = self._normalizer.normalize(text)
        lang = self._detect_language(norm.normalized)
        return self._entity_extractor.extract(norm.normalized)


def create_language_engine(
    config: Optional[PipelineConfig] = None,
) -> LanguageEngine:
    """Factory untuk membuat language engine."""
    return LanguageEngine(config=config)
