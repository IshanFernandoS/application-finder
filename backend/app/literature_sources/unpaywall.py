from __future__ import annotations

from typing import Optional

from .http import get_json


class UnpaywallSource:
    source_name = "unpaywall"

    def __init__(self, email: str):
        self.email = email

    def lookup(self, doi: str) -> Optional[dict]:
        if not doi:
            return None
        return get_json(f"https://api.unpaywall.org/v2/{doi}", {"email": self.email})
