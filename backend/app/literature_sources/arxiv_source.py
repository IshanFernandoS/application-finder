from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import List

from .base import LiteratureSearchResult, LiteratureSource


class ArxivSource(LiteratureSource):
    source_name = "arxiv"

    def search(self, query: str, limit: int = 10) -> List[LiteratureSearchResult]:
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
            {"search_query": "all:" + query, "start": 0, "max_results": limit}
        )
        with urllib.request.urlopen(url, timeout=25) as response:  # nosec - public API
            root = ET.fromstring(response.read())
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results: List[LiteratureSearchResult] = []
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", default="Untitled", namespaces=ns) or "").strip()
            authors = [
                (author.findtext("atom:name", default="", namespaces=ns) or "").strip()
                for author in entry.findall("atom:author", ns)
            ]
            published = entry.findtext("atom:published", default="", namespaces=ns) or ""
            year_match = re.match(r"(\d{4})", published)
            entry_url = entry.findtext("atom:id", default="", namespaces=ns)
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                    pdf_url = link.attrib.get("href", "")
                    break
            results.append(
                LiteratureSearchResult(
                    title=" ".join(title.split()),
                    authors=[a for a in authors if a],
                    year=int(year_match.group(1)) if year_match else None,
                    doi=None,
                    url=entry_url,
                    source=self.source_name,
                    abstract=" ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split()),
                    extra={"pdf_url": pdf_url} if pdf_url else {},
                )
            )
        return results
