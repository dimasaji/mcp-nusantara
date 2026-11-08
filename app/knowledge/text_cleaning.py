"""Conservative Haystack cleaning with immutable source text retained separately."""
import json
import os
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

# Also covers CLI/intake callers that do not import the FastAPI entrypoint.
os.environ['HAYSTACK_TELEMETRY_ENABLED'] = 'False'

CLEANING_PROFILE = 'haystack-2.31.1/horizontal-space-v1'


@lru_cache(maxsize=1)
def _cleaner():
    from haystack.components.preprocessors.document_cleaner import DocumentCleaner

    return DocumentCleaner(
        remove_empty_lines=False, remove_extra_whitespaces=False,
        remove_repeated_substrings=False, keep_id=True,
        replace_regexes={r'(?<=\S)[ \t]{2,}(?=\S)': ' '},
    )


def clean_text(text: str) -> str:
    """Keep line endings, indentation, Markdown tables and fenced code verbatim.

    Haystack's generic whitespace collapsing flattens lists/tables. Instead,
    only repeated horizontal spaces *between* words on prose lines change.
    """
    from haystack import Document

    lines = text.splitlines(keepends=True)
    prose, positions = [], []
    fence = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        marker = '```' if stripped.startswith('```') else '~~~' if stripped.startswith('~~~') else None
        if marker:
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence or '|' in line or line.startswith(('    ', '\t')):
            continue
        positions.append(index)
        prose.append(Document(content=line))
    if prose:
        for index, document in zip(positions, _cleaner().run(documents=prose)['documents'], strict=True):
            lines[index] = document.content
    return ''.join(lines)


def persist_intake_text(source: Path, document_id: str, digest: str, raw: str,
                        cleaned: str, raw_pages: list[str] | None,
                        cleaned_pages: list[str] | None) -> dict:
    """Keep the immutable source folder separate from derived text artifacts."""
    folder = source.parent.parent / 'text-extractions'
    folder.mkdir(parents=True, exist_ok=True)
    result = {'profile': CLEANING_PROFILE, 'directory': folder.name}
    for name, text, pages in [('raw', raw, raw_pages), ('cleaned', cleaned, cleaned_pages)]:
        target = folder / (source.name + f'.horizontal-space-v1.{name}.json')
        payload = {'document_id': document_id, 'source_sha256': digest,
                   'profile': CLEANING_PROFILE, 'text': text, 'pages': pages}
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        temporary.replace(target)
        result[name + '_file'] = target.name
    return result


def clean_extraction(payload: dict) -> dict:
    """Clean prose projections; preserve native JSON, cells, geometry and rows."""
    cleaned = deepcopy(payload)
    if 'raw_extraction' not in cleaned:
        cleaned['raw_extraction'] = {
            key: deepcopy(payload[key]) for key in
            ('blocks', 'markdown', 'full_document_text', 'activity_rows', 'page_count')
            if key in payload
        }
    for block in cleaned.get('blocks', []):
        if block.get('type') == 'text':
            block['content'] = clean_text(block['content'])
    for key in ('markdown', 'full_document_text'):
        if key in cleaned:
            cleaned[key] = clean_text(cleaned[key])
    cleaned['text_cleaning'] = {'profile': CLEANING_PROFILE}
    return cleaned
