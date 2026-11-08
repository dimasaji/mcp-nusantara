"""Probe authorized knowledge before dismissing a substantive chat question."""
import re

_STOP_WORDS = set(('apa itu bagaimana cara saya ingin mau tolong bantu jelaskan ceritakan '
                   'tentang mengenai dong bisa untuk dan atau dari yang dengan tersebut '
                   'mengurus membuat melakukan proses layanan apakah berikan penjelasan '
                   'sistem informasi data administrasi dokumen umum contoh pengetahuan fungsi').split())
_SMALL_TALK = re.compile(r'\s*(?:(?:halo|hallo|hai|hi|selamat pagi|selamat siang|selamat sore|'
                         r'selamat malam|terima kasih|makasih|thanks|oke|baik)[\s,.!?]*)+\s*', re.I)


def should_probe_knowledge(question):
    if _SMALL_TALK.fullmatch(question):
        return False
    return bool(_terms(question))


def _terms(text):
    return {word for word in re.findall(r'\w+', text.casefold())
            if len(word) > 2 and word not in _STOP_WORDS}


def grounded_probe_candidates(question, evidence):
    """A model-chat probe requires topical overlap as well as RAG acceptance.

    This is an additional selection guard, not permission or factual grounding.
    The existing final response/source validator still decides what may be said.
    """
    terms = _terms(question)
    selected = []
    for item in evidence:
        read = item.get if isinstance(item, dict) else lambda key, default='': getattr(item, key, default)
        title_words = _terms(str(read('title', '')))
        body_words = _terms(str(read('chunk', '')))
        title_hits = terms & title_words
        body_hits = terms & body_words
        if title_hits or (len(body_hits) >= 2 and len(body_hits) * 2 >= len(terms)):
            selected.append(item)
    return selected
