"""Validate document references against the actual context provided by storage."""
import re


def citations_supported(answer, blocks):
    pages = {p for b in blocks for p in b['page_numbers']}
    identifiers = {b['block_id'] for b in blocks}
    cited_pages = set()
    for match in re.findall(r'\b(?:halaman|hlm\.?)\s*[:#]?\s*(\d+(?:\s*(?:,|dan|&|sampai|hingga|-|–)\s*\d+)*)', answer, re.I):
        cited_pages.update(int(p) for p in re.findall(r'\d+', match))
        for start, end in re.findall(r'(\d+)\s*(?:-|–|sampai|hingga)\s*(\d+)', match, re.I):
            start, end = int(start), int(end)
            if end < start or end - start + 1 > len(pages):
                return False
            cited_pages.update(range(start, end + 1))
    cited_blocks = {value.rstrip('.,:') for value in re.findall(r'\bblok\s+([#/\w.:-]+)', answer, re.I)}
    return cited_pages.issubset(pages) and cited_blocks.issubset(identifiers)
