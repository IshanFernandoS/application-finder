from __future__ import annotations

import re
from typing import List


INLINE_CITATION_RE = re.compile(r"\[(?:\d+|[A-Za-z][^\]]{0,80}\d{4}[^\]]*)\]|\((?:[A-Z][A-Za-z-]+ et al\.,? )?\d{4}\)")


def extract_inline_citations(text: str) -> List[str]:
    return sorted(set(match.group(0) for match in INLINE_CITATION_RE.finditer(text)))
