"""Worker transport must preserve PDF text under Windows legacy encodings."""
import sys

from app.language.semantic.indobert_client import IndoBERTClient


def test_worker_transport_preserves_unicode_under_legacy_windows_encoding(tmp_path, monkeypatch):
    monkeypatch.setenv('PYTHONIOENCODING', 'cp1252:surrogateescape')
    worker = tmp_path / 'echo_worker.py'
    worker.write_text(
        "import json,sys\n"
        "for line in sys.stdin:\n"
        " value=json.loads(line)\n"
        " print(json.dumps({'ok':True,'text':value['text']},ensure_ascii=True),flush=True)\n",
        encoding='utf-8',
    )
    client = IndoBERTClient(sys.executable, str(worker), response_timeout_s=5)
    text = 'Persyaratan \u2014 surat permohonan \u2265 lengkap.'
    try:
        result = client.encode(text)
        assert result['ok']
        assert result['text'] == text
    finally:
        client.stop()
