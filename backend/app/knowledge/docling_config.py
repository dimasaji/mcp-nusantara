"""Canonical worker configuration and fingerprints of local extraction assets."""
import hashlib
import importlib.metadata
import os
import shutil
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
LEGACY_TESSERACT = Path('C:/Program Files/Tesseract-OCR/tesseract.exe')
CONFIG = {'device': 'cpu', 'threads': 1, 'ocr': 'tesseract_cli', 'languages': ['ind', 'eng'],
          'force_full_page_ocr': False, 'tables': True, 'timeout_seconds': 900,
          'ocr_policy': 'native-text-first', 'normalization_version': 'source-cell-core-5', 'tesseract_psm': 6, 'table_cell_matching': True, 'table_mode': 'accurate', 'preprocess_images': False}
_hashes = {}


def _hash(path):
    stat = path.stat()
    key = (str(path), stat.st_size, stat.st_mtime_ns)
    if key not in _hashes:
        with path.open('rb') as stream:
            _hashes[key] = hashlib.file_digest(stream, 'sha256').hexdigest()
    return _hashes[key]


def tesseract_command() -> str | None:
    """Resolve the OCR executable without assuming a Windows installation."""
    configured_path = os.getenv('NUSANTARA_TESSERACT_CMD')
    if configured_path:
        return str(Path(configured_path).expanduser())
    found = shutil.which('tesseract')
    if found:
        return found
    return str(LEGACY_TESSERACT) if LEGACY_TESSERACT.is_file() else None


def effective_config():
    """Return the extraction snapshot, degrading cleanly when OCR is unavailable."""
    command = tesseract_command()
    command_path = Path(command).resolve() if command else None
    configured_tessdata = os.getenv('TESSDATA_PREFIX')
    if configured_tessdata:
        tessdata = Path(configured_tessdata).expanduser()
    elif command_path:
        tessdata = command_path.parent / 'tessdata'
    else:
        tessdata = None
    models = PROJECT / 'nusantara-models/docling'
    artifacts = {str(p.relative_to(models)): _hash(p) for p in sorted(models.rglob('*'))
                 if p.is_file() and p.suffix.lower() in {'.json', '.safetensors', '.pt', '.onnx', '.bin', '.model'}}
    packages = {d.metadata['Name']: d.version for d in importlib.metadata.distributions(
        path=[str(PROJECT / '.venv-docling/Lib/site-packages')])
                if d.metadata['Name'].lower() in {'docling', 'docling-core', 'docling-parse', 'docling-ibm-models', 'pymupdf', 'torch'}}
    tesseract_sha256 = _hash(command_path) if command_path and command_path.is_file() else None
    language_sha256 = {}
    if tessdata:
        for lang in CONFIG['languages']:
            traineddata = tessdata / (lang + '.traineddata')
            if traineddata.is_file():
                language_sha256[lang] = _hash(traineddata)
    ocr = 'tesseract_cli' if tesseract_sha256 else 'disabled'
    return {**CONFIG, 'ocr': ocr, 'tesseract_cmd': command or '', 'tesseract_sha256': tesseract_sha256,
            'tessdata_path': str(tessdata) if tessdata else '', 'language_sha256': language_sha256,
            'model_sha256': artifacts, 'packages': packages}
