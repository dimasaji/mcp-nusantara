"""Canonical worker configuration and fingerprints of local extraction assets."""
import hashlib
import importlib.metadata
import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
CONFIG = {'device': 'cpu', 'threads': 2, 'ocr': 'tesseract_cli', 'languages': ['ind', 'eng'],
          'force_full_page_ocr': False, 'tables': True, 'timeout_seconds': 600,
          'ocr_policy': 'native-text-first', 'normalization_version': 'ruled-grid-coverage-2'}
_hashes = {}


def _hash(path):
    stat = path.stat()
    key = (str(path), stat.st_size, stat.st_mtime_ns)
    if key not in _hashes:
        with path.open('rb') as stream:
            _hashes[key] = hashlib.file_digest(stream, 'sha256').hexdigest()
    return _hashes[key]


def effective_config():
    command = Path(os.getenv('NUSANTARA_TESSERACT_CMD', 'C:/Program Files/Tesseract-OCR/tesseract.exe')).resolve()
    tessdata = Path(os.getenv('TESSDATA_PREFIX', str(command.parent / 'tessdata')))
    models = PROJECT / 'nusantara-models/docling'
    artifacts = {str(p.relative_to(models)): _hash(p) for p in sorted(models.rglob('*'))
                 if p.is_file() and p.suffix.lower() in {'.json', '.safetensors', '.pt', '.onnx', '.bin', '.model'}}
    packages = {d.metadata['Name']: d.version for d in importlib.metadata.distributions(
        path=[str(PROJECT / '.venv-docling/Lib/site-packages')])
                if d.metadata['Name'].lower() in {'docling', 'docling-core', 'docling-parse', 'docling-ibm-models', 'pymupdf', 'torch'}}
    return {**CONFIG, 'tesseract_cmd': str(command), 'tesseract_sha256': _hash(command),
            'tessdata_path': str(tessdata), 'language_sha256': {lang: _hash(tessdata / (lang + '.traineddata')) for lang in CONFIG['languages']},
            'model_sha256': artifacts, 'packages': packages}
