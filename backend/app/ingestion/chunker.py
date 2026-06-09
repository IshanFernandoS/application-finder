from __future__ import annotations

from typing import Iterable, List


def chunk_text(text: str, max_chars: int = 1800, overlap: int = 180) -> List[str]:
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return [clean] if clean else []
    chunks: List[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + max_chars)
        if end < len(clean):
            sentence_break = clean.rfind(". ", start, end)
            if sentence_break > start + max_chars // 2:
                end = sentence_break + 1
        chunks.append(clean[start:end].strip())
        if end >= len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def chunk_pages(pages: Iterable[tuple], max_chars: int = 1800) -> List[tuple]:
    out: List[tuple] = []
    for page, section, text in pages:
        for chunk in chunk_text(text, max_chars=max_chars):
            out.append((page, section, chunk))
    return out
