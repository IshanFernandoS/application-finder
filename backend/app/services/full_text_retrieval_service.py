from __future__ import annotations

import hashlib
import html
import ipaddress
import re
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import httpx

from ..config import settings
from ..ingestion.metadata_extractor import normalize_doi
from ..ingestion.pdf_parser import parse_pdf
from ..literature_sources.base import LiteratureSearchResult
from ..literature_sources.unpaywall import UnpaywallSource


@dataclass
class RetrievedFullText:
    source_url: str
    content_type: str
    pages: list[tuple[int | None, str, str]]
    local_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class FullTextRetrievalService:
    pdf_url_keys = {
        "pdf",
        "pdf_url",
        "url_for_pdf",
        "oa_pdf_url",
        "open_access_pdf_url",
        "full_text_pdf_url",
    }
    landing_url_keys = {
        "oa_url",
        "pmc_url",
        "full_text_url",
        "fulltext_url",
        "landing_page_url",
        "url_for_landing_page",
        "url",
    }

    def has_retrieval_lead(self, result: LiteratureSearchResult) -> bool:
        if not settings.enable_public_full_text_fetch:
            return False
        if self._arxiv_pdf_url(result) or self._pmc_url(result):
            return True
        if self._direct_candidate_urls(result):
            return True
        return bool(normalize_doi(result.doi))

    def retrieve(self, result: LiteratureSearchResult, document_id: str) -> RetrievedFullText | None:
        if not settings.enable_public_full_text_fetch:
            return None

        candidates = self._direct_candidate_urls(result)
        retrieved = self._retrieve_from_candidates(candidates, document_id, retrieval_method="metadata_oa_url")
        if retrieved:
            return retrieved

        doi = normalize_doi(result.doi)
        if not doi:
            return None
        try:
            data = UnpaywallSource(settings.unpaywall_email).lookup(doi)
        except Exception:
            return None
        if not data:
            return None
        return self._retrieve_from_candidates(
            self._unpaywall_candidate_urls(data),
            document_id,
            retrieval_method="unpaywall_open_access",
        )

    def _retrieve_from_candidates(
        self, candidates: Iterable[str], document_id: str, retrieval_method: str
    ) -> RetrievedFullText | None:
        for url in list(dict.fromkeys(candidates))[: settings.public_full_text_max_candidates]:
            try:
                data, content_type, final_url = self._fetch_public_url(url)
                parsed = self._parse_response(data, content_type, final_url, document_id)
            except Exception:
                continue
            if parsed and parsed.pages:
                parsed.metadata["retrieval_method"] = retrieval_method
                return parsed
        return None

    def _direct_candidate_urls(self, result: LiteratureSearchResult) -> list[str]:
        urls: list[str] = []
        for url in (self._arxiv_pdf_url(result), self._pmc_url(result)):
            if url:
                urls.append(url)
        urls.extend(self._extract_extra_urls(result.extra or {}))
        return self._dedupe_urls(urls)

    def _unpaywall_candidate_urls(self, data: dict[str, Any]) -> list[str]:
        urls: list[str] = []
        locations: list[Any] = []
        best = data.get("best_oa_location")
        if isinstance(best, dict):
            locations.append(best)
        locations.extend(data.get("oa_locations") or [])
        for location in locations:
            if isinstance(location, dict):
                urls.extend(self._extract_extra_urls(location, include_generic_url=True))
        return self._dedupe_urls(urls)

    def _extract_extra_urls(self, value: Any, include_generic_url: bool = False) -> list[str]:
        urls: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                normalized_key = key.lower()
                if isinstance(child, str) and (
                    normalized_key in self.pdf_url_keys
                    or normalized_key in self.landing_url_keys
                    or (include_generic_url and normalized_key == "url")
                ):
                    urls.append(child)
                else:
                    urls.extend(self._extract_extra_urls(child, include_generic_url=include_generic_url))
        elif isinstance(value, list):
            for item in value:
                urls.extend(self._extract_extra_urls(item, include_generic_url=include_generic_url))
        return urls

    def _arxiv_pdf_url(self, result: LiteratureSearchResult) -> str | None:
        candidates = [result.url or ""]
        extra = result.extra or {}
        for key in ("arxiv_id", "pdf_url"):
            value = extra.get(key)
            if isinstance(value, str):
                candidates.append(value)
        for value in candidates:
            match = re.search(r"arxiv\.org/(?:abs|pdf)/([^?#]+)", value)
            if match:
                arxiv_id = match.group(1).replace(".pdf", "")
                return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        return None

    def _pmc_url(self, result: LiteratureSearchResult) -> str | None:
        extra = result.extra or {}
        pmcid = extra.get("pmcid") or extra.get("pmc_id")
        if isinstance(pmcid, str) and pmcid.strip():
            clean = pmcid.strip()
            if not clean.upper().startswith("PMC"):
                clean = f"PMC{clean}"
            return f"https://pmc.ncbi.nlm.nih.gov/articles/{clean}/pdf/"
        return None

    def _fetch_public_url(self, url: str) -> tuple[bytes, str, str]:
        timeout = httpx.Timeout(float(settings.public_full_text_timeout_seconds))
        headers = {"User-Agent": f"ApplicationFinder/0.1 (mailto:{settings.literature_contact_email})"}
        current_url = url
        max_bytes = int(settings.public_full_text_max_pdf_mb * 1024 * 1024)
        with httpx.Client(timeout=timeout, follow_redirects=False, headers=headers) as client:
            for _ in range(6):
                self._validate_public_http_url(current_url)
                with client.stream("GET", current_url) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise ValueError("Redirect response missing location header.")
                        current_url = urljoin(current_url, location)
                        continue
                    response.raise_for_status()
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > max_bytes:
                        raise ValueError("Public full-text file exceeds configured size limit.")
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > max_bytes:
                            raise ValueError("Public full-text file exceeds configured size limit.")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                    return bytes(data), content_type, str(response.url)
        raise ValueError("Too many redirects while retrieving public full text.")

    def _validate_public_http_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Only public HTTP(S) full-text URLs are supported.")
        if parsed.username or parsed.password:
            raise ValueError("Credential-bearing URLs are not allowed.")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        for info in socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM):
            address = info[4][0]
            ip_address = ipaddress.ip_address(address)
            if (
                ip_address.is_private
                or ip_address.is_loopback
                or ip_address.is_link_local
                or ip_address.is_multicast
                or ip_address.is_reserved
                or ip_address.is_unspecified
            ):
                raise ValueError("Private or local full-text URLs are not allowed.")

    def _parse_response(
        self, data: bytes, content_type: str, source_url: str, document_id: str
    ) -> RetrievedFullText | None:
        if self._looks_like_pdf(data, content_type, source_url):
            path = self._write_pdf(data, document_id, source_url)
            pages = parse_pdf(path)
            if pages:
                return RetrievedFullText(
                    source_url=source_url,
                    content_type=content_type or "application/pdf",
                    pages=pages,
                    local_path=path,
                    metadata={"format": "pdf"},
                )
            return None

        text = self._extract_text(data, content_type)
        if len(text) < 800:
            return None
        return RetrievedFullText(
            source_url=source_url,
            content_type=content_type or "text/html",
            pages=[(None, "full_text", text)],
            metadata={"format": "html_or_text"},
        )

    def _looks_like_pdf(self, data: bytes, content_type: str, source_url: str) -> bool:
        path = urlparse(source_url).path.lower()
        return data.startswith(b"%PDF") or "pdf" in content_type or path.endswith(".pdf")

    def _write_pdf(self, data: bytes, document_id: str, source_url: str) -> Path:
        digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:10]
        path = settings.data_dir / "public_full_text" / f"{document_id}-{digest}.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def _extract_text(self, data: bytes, content_type: str) -> str:
        text = data.decode("utf-8", errors="ignore")
        if "html" in content_type or "<html" in text[:1000].lower():
            text = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", text)
            text = re.sub(r"(?s)<[^>]+>", " ", text)
            text = html.unescape(text)
        return " ".join(text.split())

    def _dedupe_urls(self, urls: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for url in urls:
            clean = str(url or "").strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            out.append(clean)
        return out
