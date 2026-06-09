from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def document_key(doi: Optional[str], title: str, path: Path) -> str:
    if doi:
        return "doi:" + doi.lower()
    title_key = " ".join(title.lower().split())[:200]
    return "title:" + title_key if title_key else "file:" + file_hash(path)
