from __future__ import annotations

from typing import List

from .base import LiteratureSearchResult, LiteratureSource
from .http import get_json


class PubMedSource(LiteratureSource):
    source_name = "pubmed"

    def search(self, query: str, limit: int = 10) -> List[LiteratureSearchResult]:
        search = get_json(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            {"db": "pubmed", "term": query, "retmode": "json", "retmax": limit},
        )
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        summary = get_json(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            {"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
        )
        results: List[LiteratureSearchResult] = []
        for pubmed_id in ids:
            item = summary.get("result", {}).get(pubmed_id, {})
            authors = [author.get("name", "") for author in item.get("authors", []) if author.get("name")]
            pubdate = item.get("pubdate") or ""
            year = int(pubdate[:4]) if pubdate[:4].isdigit() else None
            article_ids = item.get("articleids", [])
            doi = next((row.get("value") for row in article_ids if row.get("idtype") == "doi"), None)
            results.append(
                LiteratureSearchResult(
                    title=item.get("title") or "Untitled",
                    authors=authors,
                    year=year,
                    doi=doi,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/",
                    source=self.source_name,
                    abstract=None,
                    extra={"pubmed_id": pubmed_id, "source": item.get("source")},
                )
            )
        return results
