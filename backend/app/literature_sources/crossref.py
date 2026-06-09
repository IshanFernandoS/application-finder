from __future__ import annotations

from typing import List

from .base import LiteratureSearchResult, LiteratureSource
from .http import get_json


class CrossrefSource(LiteratureSource):
    source_name = "crossref"

    def search(self, query: str, limit: int = 10) -> List[LiteratureSearchResult]:
        data = get_json("https://api.crossref.org/works", {"query": query, "rows": limit})
        results: List[LiteratureSearchResult] = []
        for item in data.get("message", {}).get("items", []):
            author_names = []
            for author in item.get("author", []):
                name = " ".join(part for part in [author.get("given"), author.get("family")] if part)
                if name:
                    author_names.append(name)
            year = None
            date_parts = item.get("published-print", item.get("published-online", {})).get("date-parts", [])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
            results.append(
                LiteratureSearchResult(
                    title=(item.get("title") or ["Untitled"])[0],
                    authors=author_names,
                    year=year,
                    doi=item.get("DOI"),
                    url=item.get("URL"),
                    source=self.source_name,
                    abstract=item.get("abstract"),
                    extra={"type": item.get("type"), "publisher": item.get("publisher")},
                )
            )
        return results
