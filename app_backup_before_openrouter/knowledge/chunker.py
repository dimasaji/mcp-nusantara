from typing import List

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    if chunk_size <= 0: raise ValueError('chunk_size must be positive')
    overlap = max(0, min(overlap, chunk_size - 1))
    if not text: return []
    out=[]; start=0
    while start < len(text):
        end=min(len(text), start+chunk_size); out.append(text[start:end])
        if end == len(text): break
        start=end-overlap
    return out

class Chunker:
    def __init__(self, chunk_size=512, overlap=64): self.chunk_size=chunk_size; self.overlap=overlap
    def chunk(self, text): return chunk_text(text, self.chunk_size, self.overlap)

SentenceChunker = Chunker

ParagraphChunker = Chunker

def get_chunker(strategy="sentence", chunk_size=512, overlap=64): return Chunker(chunk_size, overlap)
