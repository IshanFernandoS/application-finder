from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from ..exceptions import DependencyUnavailableError


def parse_pdf(path: Path) -> List[Tuple[int, str, str]]:
    try:
        import fitz  # type: ignore
    except Exception:
        fitz = None

    if fitz is not None:
        chunks: List[Tuple[int, str, str]] = []
        with fitz.open(path) as doc:
            for index, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                if text:
                    chunks.append((index, "page", text))
        return chunks

    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:
        raise DependencyUnavailableError(
            "PDF ingestion requires PyMuPDF (`pymupdf`) or `pypdf`; install backend requirements."
        ) from exc

    reader = PdfReader(str(path))
    chunks = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            chunks.append((index, "page", text))
    return chunks
