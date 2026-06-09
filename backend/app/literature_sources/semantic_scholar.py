from __future__ import annotations

from typing import List, Optional

from .base import LiteratureSearchResult, LiteratureSource
from .http import get_json


class SemanticScholarSource(LiteratureSource):
    source_name = "semantic_scholar"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search(self, query: str, limit: int = 10) -> List[LiteratureSearchResult]:
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        fields = "title,authors,year,externalIds,url,abstract"
        data = get_json(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            {"query": query, "limit": limit, "fields": fields},
            headers=headers,
        )
        results: List[LiteratureSearchResult] = []
        for item in data.get("data", []):
            results.append(
                LiteratureSearchResult(
                    title=item.get("title") or "Untitled",
                    authors=[author.get("name", "") for author in item.get("authors", []) if author.get("name")],
                    year=item.get("year"),
                    doi=(item.get("externalIds") or {}).get("DOI"),
                    url=item.get("url"),
                    source=self.source_name,
                    abstract=item.get("abstract"),
                    extra={"paperId": item.get("paperId")},
                )
            )
        return results
