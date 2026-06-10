from __future__ import annotations

from typing import List, Optional

from .base import LiteratureSearchResult, LiteratureSource
from .http import get_json


class OpenAlexSource(LiteratureSource):
    source_name = "openalex"

    def __init__(self, contact_email: Optional[str] = None):
        self.contact_email = contact_email

    def search(self, query: str, limit: int = 10) -> List[LiteratureSearchResult]:
        data = get_json(
            "https://api.openalex.org/works",
            {"search": query, "per-page": limit, "mailto": self.contact_email},
        )
        results: List[LiteratureSearchResult] = []
        for item in data.get("results", []):
            authors = [
                authorship.get("author", {}).get("display_name", "")
                for authorship in item.get("authorships", [])
                if authorship.get("author", {}).get("display_name")
            ]
            doi = item.get("doi")
            if doi and isinstance(doi, str):
                doi = doi.replace("https://doi.org/", "")
            results.append(
                LiteratureSearchResult(
                    title=item.get("display_name") or "Untitled",
                    authors=authors,
                    year=item.get("publication_year"),
                    doi=doi,
                    url=item.get("id"),
                    source=self.source_name,
                    abstract=None,
                    extra={"openalex_id": item.get("id"), "cited_by_count": item.get("cited_by_count")},
                )
            )
        return results
