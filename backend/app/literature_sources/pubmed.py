from __future__ import annotations

from typing import List, Optional

from .base import LiteratureSearchResult, LiteratureSource
from .http import get_json


class PubMedSource(LiteratureSource):
    source_name = "pubmed"
    summary_batch_size = 100

    def __init__(self, contact_email: Optional[str] = None):
        self.contact_email = contact_email

    def search(self, query: str, limit: int = 10) -> List[LiteratureSearchResult]:
        requested = max(1, int(limit or 10))
        search = get_json(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": requested,
                "tool": "ApplicationFinder",
                "email": self.contact_email,
            },
        )
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        results: List[LiteratureSearchResult] = []
        for start in range(0, len(ids), self.summary_batch_size):
            batch_ids = ids[start : start + self.summary_batch_size]
            summary = get_json(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                {"db": "pubmed", "id": ",".join(batch_ids), "retmode": "json"},
            )
            for pubmed_id in batch_ids:
                item = summary.get("result", {}).get(pubmed_id, {})
                authors = [author.get("name", "") for author in item.get("authors", []) if author.get("name")]
                pubdate = item.get("pubdate") or ""
                year = int(pubdate[:4]) if pubdate[:4].isdigit() else None
                article_ids = item.get("articleids", [])
                doi = next((row.get("value") for row in article_ids if row.get("idtype") == "doi"), None)
                pmcid = next((row.get("value") for row in article_ids if row.get("idtype") in {"pmc", "pmcid"}), None)
                results.append(
                    LiteratureSearchResult(
                        title=item.get("title") or "Untitled",
                        authors=authors,
                        year=year,
                        doi=doi,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/",
                        source=self.source_name,
                        abstract=None,
                        extra={"pubmed_id": pubmed_id, "pmcid": pmcid, "source": item.get("source")},
                    )
                )
        return results
