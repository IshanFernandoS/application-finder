from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def extract_metadata(path: Path, text: str) -> Dict[str, object]:
    first_lines = [line.strip() for line in text.splitlines() if line.strip()][:8]
    title = first_lines[0] if first_lines else path.stem.replace("_", " ")
    doi_match = DOI_RE.search(text)
    year_match = YEAR_RE.search(text)
    return {
        "title": title[:300],
        "authors": [],
        "doi": doi_match.group(0).lower() if doi_match else None,
        "year": int(year_match.group(0)) if year_match else None,
    }


def normalize_doi(doi: Optional[str]) -> Optional[str]:
    return doi.lower().replace("https://doi.org/", "").strip() if doi else None
