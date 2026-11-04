import pytest

from app.api.routes import _arithmetic_response


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("17 + 25", "42"),
        ("hitung 17 + 25", "42"),
        ("17 ditambah 25", "42"),
        ("berapakah 100 dikurangi 58", "42"),
        ("6 dikali 7", "42"),
        ("84 dibagi 2", "42"),
        ("(10 + 4) * 3", "42"),
        ("Hitung 17 + 25. Jawab singkat dengan hasilnya.", "42"),
    ],
)
def test_safe_arithmetic(question, expected):
    assert _arithmetic_response(question) == expected


@pytest.mark.parametrize(
    "question",
    [
        "Apa fungsi KTP elektronik di Indonesia?",
        "Berapa biaya pengurusan KTP?",
        "Wajib membawa 3 fotokopi untuk paspor",
        "__import__('os').system('whoami')",
        "1 / 0",
        "",
    ],
)
def test_non_arithmetic_or_unsafe_input_is_rejected(question):
    assert _arithmetic_response(question) is None