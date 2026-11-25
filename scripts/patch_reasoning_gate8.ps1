from pathlib import Path

path = Path(".\app\reasoning\engine.py")

source = path.read_text(encoding="utf-8")

# ------------------------------------------------------------
# PATCH _text()
# ------------------------------------------------------------
old_text = '''    def _text(self, item):
        return str(getattr(item, "text", "") or "").strip()
'''

new_text = '''    def _text(self, item):
        if isinstance(item, dict):
            for key in ("text", "content", "snippet", "source_text", "chunk_text"):
                value = item.get(key)
                if value:
                    return str(value).strip()

        for key in ("text", "content", "snippet", "source_text", "chunk_text"):
            value = getattr(item, key, None)
            if value:
                return str(value).strip()

        return str(item).strip() if item else ""
'''

if old_text in source:
    source = source.replace(old_text, new_text)
elif new_text not in source:
    raise SystemExit("PATCH _text(): target tidak ditemukan")

# ------------------------------------------------------------
# PATCH _score()
# ------------------------------------------------------------
old_score = '''    def _score(self, item):
        try:
            return float(getattr(item, "score", 0.0) or 0.0)
        except (TypeError, ValueError):
            return 0.0
'''

new_score = '''    def _score(self, item):
        try:
            if isinstance(item, dict):
                for key in ("score", "relevance_score", "similarity", "confidence"):
                    value = item.get(key)
                    if value is not None:
                        return float(value or 0.0)

            for key in ("score", "relevance_score", "similarity", "confidence"):
                value = getattr(item, key, None)
                if value is not None:
                    return float(value or 0.0)

        except (TypeError, ValueError):
            return 0.0

        return 0.0
'''

if old_score in source:
    source = source.replace(old_score, new_score)
elif new_score not in source:
    raise SystemExit("PATCH _score(): target tidak ditemukan")

path.write_text(source, encoding="utf-8")

print("ReasoningEngine evidence adapter: PATCHED")
