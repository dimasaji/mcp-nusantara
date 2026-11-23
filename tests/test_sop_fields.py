"""Unit tests for app.knowledge.sop_fields (deterministic SOP field extraction)."""
import pytest

from app.knowledge.sop_fields import extract_sop_fields, compose_answer


def test_extract_basic_fields():
    text = (
        "NAMA SOP: Permohonan KTP\n"
        "Persyaratan: Fotokopi KK, KTP lama\n"
        "Prosedur: Datang ke loket, isi formulir\n"
        "Durasi: 3 hari kerja\n"
        "Biaya: gratis\n"
        "Dasar Hukum: UU No. 24 Tahun 2013\n"
        "Penerbitan KTP baru\n"
    )
    fields = extract_sop_fields(text)
    assert fields["title"] == "Permohonan KTP"
    assert fields["requirements"] == "Fotokopi KK, KTP lama"
    assert fields["procedure"] == "Datang ke loket, isi formulir"
    assert fields["duration"] == "3 hari kerja"
    assert fields["cost"] == "gratis"
    assert fields["legal_basis"] == "UU No. 24 Tahun 2013"
    assert fields["product"] == "KTP baru"
    assert fields["channel"] == "loket"


def test_legal_basis_inline_value():
    text = "Dasar Hukum: Peraturan Menteri Dalam Negeri Nomor 10 Tahun 2020"
    fields = extract_sop_fields(text)
    assert fields["legal_basis"] == "Peraturan Menteri Dalam Negeri Nomor 10 Tahun 2020"


def test_legal_basis_multiline():
    text = (
        "Dasar Hukum\n"
        "UU No. 24 Tahun 2013\n"
        "Permen Dalam Negeri No. 10 Tahun 2020\n"
        "Peringatan: jangan terlambat\n"
    )
    fields = extract_sop_fields(text)
    assert "UU No. 24 Tahun 2013" in fields["legal_basis"]
    assert "Permen Dalam Negeri No. 10 Tahun 2020" in fields["legal_basis"]


def test_empty_text_returns_empty_fields():
    fields = extract_sop_fields("")
    assert all(v == "" for v in fields.values())
    assert set(fields.keys()) == {
        "title", "requirements", "procedure", "duration", "cost",
        "legal_basis", "product", "channel",
    }


def test_none_text():
    fields = extract_sop_fields(None)
    assert all(v == "" for v in fields.values())


def test_requirements_multiline_bullets():
    text = (
        "Persyaratan:\n"
        "- Fotokopi KK\n"
        "- KTP lama\n"
        "- Surat Permohonan\n"
        "Prosedur: Datang ke loket\n"
    )
    fields = extract_sop_fields(text)
    assert "Fotokopi KK" in fields["requirements"]
    assert "KTP lama" in fields["requirements"]
    assert "Surat Permohonan" in fields["requirements"]

def test_procedure_multiline_bullets():
    text = (
        "Prosedur:\n"
        "1. Datang ke loket\n"
        "2. Isi formulir\n"
        "3. Serahkan berkas\n"
        "Durasi: 3 hari\n"
    )
    fields = extract_sop_fields(text)
    assert "Datang ke loket" in fields["procedure"]
    assert "Isi formulir" in fields["procedure"]
    assert "Serahkan berkas" in fields["procedure"]
    fields = {"requirements": "Fotokopi KK", "procedure": "", "duration": "",
              "cost": "", "legal_basis": "", "product": "", "channel": "", "title": ""}
    assert compose_answer(fields, "apa persyaratannya?") == "Persyaratan: Fotokopi KK"


def test_compose_answer_no_match_returns_empty():
    fields = {"requirements": "Fotokopi KK", "procedure": "", "duration": "",
              "cost": "", "legal_basis": "", "product": "", "channel": "", "title": ""}
    assert compose_answer(fields, "halo") == ""


def test_compose_answer_multiple():
    fields = {"requirements": "Fotokopi KK", "procedure": "Datang ke loket",
              "duration": "3 hari", "cost": "gratis", "legal_basis": "",
              "product": "", "channel": "loket", "title": ""}
    out = compose_answer(fields, "persyaratan prosedur biaya durasi kanal")
    assert "Persyaratan: Fotokopi KK" in out
    assert "Prosedur: Datang ke loket" in out
    assert "Waktu: 3 hari" in out
    assert "Biaya: gratis" in out
    assert "Kanal: loket" in out
