from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import List

from .base import LiteratureSearchResult


def import_zotero_csv(path: Path) -> List[LiteratureSearchResult]:
    rows: List[LiteratureSearchResult] = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            creators = row.get("Author") or row.get("Authors") or ""
            rows.append(
                LiteratureSearchResult(
                    title=row.get("Title") or "Untitled",
                    authors=[part.strip() for part in creators.split(";") if part.strip()],
                    year=int(row["Publication Year"]) if row.get("Publication Year", "").isdigit() else None,
                    doi=row.get("DOI") or None,
                    url=row.get("Url") or row.get("URL") or None,
                    source="zotero",
                    abstract=row.get("Abstract Note") or None,
                    extra={k: v for k, v in row.items() if v},
                )
            )
    return rows


def import_bibtex(path: Path) -> List[LiteratureSearchResult]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries = re.split(r"\n@", "\n" + text)
    rows: List[LiteratureSearchResult] = []
    for entry in entries:
        if not entry.strip():
            continue
        fields = {key.lower(): value.strip("{}\" ") for key, value in re.findall(r"(\w+)\s*=\s*[{'\"]([^{}'\"]+)[}'\"]", entry)}
        title = fields.get("title") or "Untitled"
        authors = [author.strip() for author in fields.get("author", "").replace(" and ", ";").split(";") if author.strip()]
        year = int(fields["year"]) if fields.get("year", "").isdigit() else None
        rows.append(
            LiteratureSearchResult(
                title=title,
                authors=authors,
                year=year,
                doi=fields.get("doi"),
                url=fields.get("url"),
                source="zotero_bibtex",
                abstract=fields.get("abstract"),
                extra=fields,
            )
        )
    return rows


def import_ris(path: Path) -> List[LiteratureSearchResult]:
    rows: List[LiteratureSearchResult] = []
    current = {}
    authors: List[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if len(raw_line) < 6 or "  - " not in raw_line:
            continue
        tag, value = raw_line[:2], raw_line[6:].strip()
        if tag == "TY":
            current = {"type": value}
            authors = []
        elif tag == "AU":
            authors.append(value)
        elif tag == "TI":
            current["title"] = value
        elif tag == "PY":
            current["year"] = value[:4]
        elif tag == "DO":
            current["doi"] = value
        elif tag == "UR":
            current["url"] = value
        elif tag == "AB":
            current["abstract"] = value
        elif tag == "ER":
            rows.append(
                LiteratureSearchResult(
                    title=current.get("title") or "Untitled",
                    authors=authors,
                    year=int(current["year"]) if str(current.get("year", "")).isdigit() else None,
                    doi=current.get("doi"),
                    url=current.get("url"),
                    source="zotero_ris",
                    abstract=current.get("abstract"),
                    extra=current,
                )
            )
            current = {}
            authors = []
    return rows


def import_zotero_file(path: Path) -> List[LiteratureSearchResult]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return import_zotero_csv(path)
    if suffix == ".bib":
        return import_bibtex(path)
    if suffix == ".ris":
        return import_ris(path)
    return []
