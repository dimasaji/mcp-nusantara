"""Synthetic model text over temporary source files; no real model or service."""
import asyncio
import json
import pytest

from app.devcore import DevCore

SOURCE = 'import urllib.request\nurllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)\n'
UNSUPPORTED = 'Script ini menampilkan hasil ke layar dan melakukan retry dengan timeout 10 detik.'
SUPPORTED = 'Tidak ada print(). Request HTTP ke localhost dengan timeout 3 detik. Tidak ada retry.'


def workspace(tmp_path):
    (tmp_path/'healthcheck.py').write_text(SOURCE, encoding='utf-8')
    return tmp_path


def test_rejected_model_analysis_is_not_the_human_answer(tmp_path):
    root = workspace(tmp_path)
    core = DevCore(str(root), generate=lambda _: UNSUPPORTED)
    before = (root/'healthcheck.py').read_bytes()
    result = asyncio.run(core.handle('Baca healthcheck.py dan jelaskan'))
    assert result['verification']['status'] == 'failed'
    assert {v['rule'] for v in result['verification']['violations']} >= {
        'print/menampilkan hasil', 'retry/pengulangan', 'nilai timeout tidak sesuai source'}
    assert UNSUPPORTED not in result['answer']
    assert 'timeout 10' not in result['answer']
    assert 'PERINGATAN' in result['answer']
    assert 'timeout=3' in result['answer']
    assert 'Tidak ada panggilan print()' in result['answer']
    assert (root/'healthcheck.py').read_bytes() == before
    assert core.audit.verify()
    assert UNSUPPORTED not in json.dumps(core.audit.entries())


def test_supported_model_analysis_is_preserved(tmp_path):
    core = DevCore(str(workspace(tmp_path)), generate=lambda _: SUPPORTED)
    result = asyncio.run(core.handle('Baca healthcheck.py dan jelaskan'))
    assert result['verification'] == {'status': 'passed', 'violations': []}
    assert SUPPORTED in result['answer']
    assert 'PERINGATAN' not in result['answer']


def test_missing_model_response_keeps_existing_static_fallback(tmp_path):
    core = DevCore(str(workspace(tmp_path)))
    result = asyncio.run(core.handle('Baca healthcheck.py dan jelaskan'))
    assert result['verification'] == {'status': 'fallback_static_facts', 'violations': []}
    assert 'timeout=3' in result['answer']
    assert 'Analisis model tidak tersedia' in result['answer']


def test_rejected_analysis_does_not_enable_requested_edits(tmp_path):
    root = workspace(tmp_path)
    core = DevCore(str(root), generate=lambda _: UNSUPPORTED)
    result = asyncio.run(core.handle('Perbaiki healthcheck.py dan jelaskan'))
    assert result['modify_blocked'] is True
    assert result['verification']['status'] == 'failed'
    assert UNSUPPORTED not in result['answer']
    assert 'read-only' in result['answer']
    assert {call['name'] for call in result['tool']['calls']} <= {'find_file', 'read_file'}
    assert (root/'healthcheck.py').read_text(encoding='utf-8') == SOURCE


def test_mixed_negation_does_not_hide_unsupported_positive_claim(tmp_path):
    root = tmp_path / 'workspace'
    (root / 'app').mkdir(parents=True)
    (root / 'app/example.py').write_text('print("fixture")\n', encoding='utf-8')
    mixed = 'Script mencetak hasil, tidak ada retry, tetapi script menyimpan response ke file.'
    result = DevCore(str(root), generate=lambda _: mixed).handle_sync('Analisis app/example.py')
    assert result['verification']['status'] == 'failed'
    assert {v['rule'] for v in result['verification']['violations']} == {'penyimpanan response/file'}
    assert mixed not in result['answer']


def test_negation_after_positive_claim_and_adjacent_claims():
    from app.devcore.grounding import check_grounding
    for claim in ('Script menyimpan response tanpa retry.',
                  'Tidak ada retry script menyimpan response ke file.',
                  'Tidak ada retry dan script menyimpan response ke file.'):
        assert any(v.rule == 'penyimpanan response/file' for v in check_grounding(claim, 'x = 1\n'))
    assert not check_grounding('Tidak ada print(). Tidak ada retry.', 'x = 1\n')


def test_truncated_source_is_incomplete_and_callback_not_invoked(tmp_path):
    (tmp_path / 'app').mkdir()
    prefix = 'x = 1\n' + '# padding\n' * 8
    (tmp_path / 'app/example.py').write_bytes((prefix + 'print("later")\n').encode())
    calls = []
    core = DevCore(str(tmp_path), generate=lambda _: calls.append(True) or 'Tidak ada print().')
    core.ws.max_read_bytes = len(prefix.encode())
    result = core.handle_sync('Analisis app/example.py')
    assert result['tool']['result']['truncated']
    assert result['verification']['status'] == 'incomplete_source'
    assert result['verification']['evidence_completeness'] == 'incomplete'
    assert 'Source terpotong' in result['answer'] and 'fragmen' in result['answer']
    assert not calls
    complete = DevCore(str(tmp_path), generate=lambda _: 'Script mencetak hasil.').handle_sync('Analisis app/example.py')
    assert complete['verification']['status'] == 'passed'
    assert not complete['tool']['result']['truncated']


def test_truncated_source_without_callback_and_verbatim_keeps_limitation(tmp_path):
    (tmp_path / 'app').mkdir()
    (tmp_path / 'app/example.py').write_bytes(b'x = 1\nprint("later")\n')
    core = DevCore(str(tmp_path))
    core.ws.max_read_bytes = 6
    result = core.handle_sync('Baca app/example.py dan tampilkan isi persis')
    assert result['verification']['status'] == 'incomplete_source'
    assert '(dipotong)' in result['answer'] and 'Source terpotong' in result['answer']


@pytest.mark.parametrize('decimal', ['1,5', '3,5', '10,25', '0,75'])
@pytest.mark.parametrize('matches', [False, True])
def test_decimal_comma_timeout_value_is_preserved(decimal, matches):
    from app.devcore.grounding import check_grounding
    value = decimal.replace(',', '.') if matches else decimal.split(',')[0]
    source = f'request(timeout={value})'
    claim = f'Request menggunakan timeout {decimal} detik.'
    violations = check_grounding(claim, source)
    assert {v.rule for v in violations} == (set() if matches else {'nilai timeout tidak sesuai source'})
    if not matches:
        assert decimal in violations[0].sentence


@pytest.mark.parametrize('value', ['3', '3.5'])
def test_decimal_comma_fix_preserves_integer_and_dot_decimal(value):
    from app.devcore.grounding import check_grounding
    assert not check_grounding(f'Request menggunakan timeout {value} detik.', f'request(timeout={value})')


@pytest.mark.parametrize(('claim', 'expected'), [
    ('Request tidak menggunakan timeout 3 detik.', set()),
    ('Request tidak menggunakan timeout 3,5 detik.', set()),
    ('Tidak ada retry, tetapi Request menggunakan timeout 3,5 detik.', {'nilai timeout tidak sesuai source'}),
    ('Request menggunakan timeout 3,5 detik, tidak ada retry.', {'nilai timeout tidak sesuai source'}),
    ('Request menggunakan timeout 3 detik, tidak ada retry, tetapi menyimpan response ke file.',
     {'penyimpanan response/file'}),
])
def test_decimal_comma_fix_preserves_local_and_clause_negation(claim, expected):
    from app.devcore.grounding import check_grounding
    assert {v.rule for v in check_grounding(claim, 'request(timeout=3)')} == expected


def test_decimal_comma_mixed_supported_value_and_unsupported_claim():
    from app.devcore.grounding import check_grounding
    claim = 'Request menggunakan timeout 3,5 detik, tidak ada retry, tetapi menyimpan response ke file.'
    assert {v.rule for v in check_grounding(claim, 'request(timeout=3.5)')} == {'penyimpanan response/file'}


def test_decimal_comma_mismatch_is_rejected_in_human_answer(tmp_path):
    core = DevCore(str(workspace(tmp_path)), generate=lambda _: 'Request menggunakan timeout 3,5 detik.')
    result = core.handle_sync('Baca healthcheck.py dan jelaskan')
    assert result['verification']['status'] == 'failed'
    assert {v['rule'] for v in result['verification']['violations']} == {'nilai timeout tidak sesuai source'}
    assert 'Request menggunakan timeout 3,5 detik.' not in result['answer']
    assert 'timeout=3' in result['answer']


def test_decimal_comma_matching_value_is_retained_in_human_answer(tmp_path):
    (tmp_path / 'example.py').write_text('request(timeout=3.5)\n', encoding='utf-8')
    claim = 'Request menggunakan timeout 3,5 detik.'
    result = DevCore(str(tmp_path), generate=lambda _: claim).handle_sync('Baca example.py dan jelaskan')
    assert result['verification']['status'] == 'passed' and claim in result['answer']
