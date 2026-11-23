"""Conservative, local preparation before Knowledge indexing.

Never rewrite facts or collapse layout. Replacements have identical character
length so physical page offsets remain valid. The original file is untouched.
"""
from __future__ import annotations

import hashlib
import unicodedata
from collections import Counter

PREPARATION_VERSION = 'offset-preserving-1'


def prepare_knowledge_text(text: str) -> tuple[str, dict]:
    """Return indexable text and a versioned quality summary, or reject it."""
    cleaned = ''.join(
        (' ' if text[index + 1:index + 2] == '\n' else '\n') if char == '\r' else
        ' ' if (unicodedata.category(char) in {'Cc', 'Cf', 'Zs'}
                and char not in {'\n', '\t'}) else char
        for index, char in enumerate(text)
    )
    normalized = ' '.join(cleaned.split())
    if len(normalized) < 40:
        raise ValueError('EXTRACTED_TEXT_TOO_SHORT_OR_SCANNED; OCR_REQUIRED')
    visible = [char for char in cleaned if not char.isspace()]
    counts = Counter(visible)
    # Length-independent heuristics detect obvious extraction failures only;
    # these do not establish semantic correctness or replace source approval.
    alphanumeric_ratio = sum(char.isalnum() for char in visible) / len(visible)
    if (alphanumeric_ratio < 0.25 or counts.get('\ufffd', 0) / len(visible) > 0.02
            or counts.most_common(1)[0][1] / len(visible) > 0.90):
        raise ValueError('EXTRACTED_TEXT_QUALITY_CHECK_FAILED')
    return cleaned, {
        'version': PREPARATION_VERSION,
        'status': 'VALID',
        'changed_characters': sum(a != b for a, b in zip(text, cleaned, strict=True)),
        'alphanumeric_ratio': round(alphanumeric_ratio, 4),
        'text_sha256': hashlib.sha256(cleaned.encode('utf-8')).hexdigest(),
    }
