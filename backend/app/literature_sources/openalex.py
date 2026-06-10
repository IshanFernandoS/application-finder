from __future__ import annotations

from typing import List, Optional

from .base import LiteratureSearchResult, LiteratureSource
from .http import get_json


class OpenAlexSource(LiteratureSource):
    source_name = "openalex"
    page_size = 200

    def __init__(self, contact_email: Optional[str] = None):
        self.contact_email = contact_email

    def search(self, query: str, limit: int = 10) -> List[LiteratureSearchResult]:
        results: List[LiteratureSearchResult] = []
        requested = max(1, int(limit or 10))
        cursor = "*"
        while len(results) < requested:
            page_limit = min(self.page_size, requested - len(results))
            data = get_json(
                "https://api.openalex.org/works",
                {"search": query, "per-page": page_limit, "cursor": cursor, "mailto": self.contact_email},
            )
            items = data.get("results", [])
            if not items:
                break
            for item in items:
                authors = [
                    authorship.get("author", {}).get("display_name", "")
                    for authorship in item.get("authorships", [])
                    if authorship.get("author", {}).get("display_name")
                ]
                doi = item.get("doi")
                if doi and isinstance(doi, str):
                    doi = doi.replace("https://doi.org/", "")
                abstract = _abstract_from_inverted_index(item.get("abstract_inverted_index"))
                results.append(
                    LiteratureSearchResult(
                        title=item.get("display_name") or "Untitled",
                        authors=authors,
                        year=item.get("publication_year"),
                        doi=doi,
                        url=item.get("id"),
                        source=self.source_name,
                        abstract=abstract,
                        extra={
                            "openalex_id": item.get("id"),
                            "cited_by_count": item.get("cited_by_count"),
                            "open_access": item.get("open_access"),
                            "primary_location": item.get("primary_location"),
                            "best_oa_location": item.get("best_oa_location"),
                        },
                    )
                )
            next_cursor = (data.get("meta") or {}).get("next_cursor")
            if not next_cursor or next_cursor == cursor or len(items) < page_limit:
                break
            cursor = next_cursor
        return results


def _abstract_from_inverted_index(value: object) -> Optional[str]:
    if not isinstance(value, dict) or not value:
        return None
    positioned_words: list[tuple[int, str]] = []
    for word, positions in value.items():
        if not isinstance(word, str) or not isinstance(positions, list):
            continue
        for position in positions:
            if isinstance(position, int):
                positioned_words.append((position, word))
    if not positioned_words:
        return None
    return " ".join(word for _, word in sorted(positioned_words))
