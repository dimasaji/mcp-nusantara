"""Structure-aware chunking for Nusantara V1.

Preserves sentence, paragraph, and table boundaries. Falls back to
character-based chunking only when no natural boundary is found.
"""
from typing import List
import re


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences, preserving table rows and paragraphs."""
    # Split on sentence boundaries (. ! ? followed by space/newline)
    # but NOT inside table rows (lines starting with |)
    lines = text.split('\n')
    sentences = []
    current = ''
    for line in lines:
        stripped = line.strip()
        # Table rows: keep as-is (don't split)
        if stripped.startswith('|') or '|' in line and line.count('|') >= 2:
            if current.strip():
                sentences.append(current.strip())
                current = ''
            sentences.append(line)
            continue
        # Empty line = paragraph boundary
        if not stripped:
            if current.strip():
                sentences.append(current.strip())
                current = ''
            continue
        current += ' ' + line
        # Sentence boundary
        if re.search(r'[.!?]\s*$', line):
            sentences.append(current.strip())
            current = ''
    if current.strip():
        sentences.append(current.strip())
    return [s for s in sentences if s.strip()]


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    if chunk_size <= 0:
        raise ValueError('chunk_size must be positive')
    overlap = max(0, min(overlap, chunk_size - 1))
    if not text:
        return []
    sentences = _split_sentences(text)
    if not sentences:
        # Fallback to character-based
        out = []
        start = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            out.append(text[start:end])
            if end == len(text):
                break
            start = end - overlap
        return out
    # Group sentences into chunks
    out = []
    current = ''
    for sent in sentences:
        if len(current) + len(sent) + 1 <= chunk_size:
            current = (current + ' ' + sent).strip() if current else sent
        else:
            if current:
                out.append(current)
            # If single sentence exceeds chunk_size, split it
            if len(sent) > chunk_size:
                start = 0
                while start < len(sent):
                    end = min(len(sent), start + chunk_size)
                    out.append(sent[start:end])
                    if end == len(sent):
                        break
                    start = end - overlap
                current = ''
            else:
                current = sent
    if current:
        out.append(current)
    # Add overlap between chunks
    if overlap > 0 and len(out) > 1:
        result = [out[0]]
        for i in range(1, len(out)):
            prev = out[i-1]
            if len(prev) <= overlap:
                overlap_text = prev
            else:
                # Word-boundary aware overlap
                start = len(prev) - overlap
                while start > 0 and prev[start] != ' ':
                    start -= 1
                overlap_text = prev[start:].strip()
            result.append(overlap_text + ' ' + out[i])
        return result
    return out


class Chunker:
    def __init__(self, chunk_size=512, overlap=64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text):
        return chunk_text(text, self.chunk_size, self.overlap)


SentenceChunker = Chunker
ParagraphChunker = Chunker


def get_chunker(strategy="sentence", chunk_size=512, overlap=64):
    return Chunker(chunk_size, overlap)
