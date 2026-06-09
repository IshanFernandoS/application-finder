from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class LiteratureSearchResult:
    title: str
    authors: List[str]
    year: Optional[int]
    doi: Optional[str]
    url: Optional[str]
    source: str
    abstract: Optional[str] = None
    extra: Optional[Dict[str, object]] = None


class LiteratureSource:
    source_name = "base"

    def search(self, query: str, limit: int = 10) -> List[LiteratureSearchResult]:
        raise NotImplementedError
