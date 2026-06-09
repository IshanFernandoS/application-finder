from __future__ import annotations

from pathlib import Path
from typing import List


def discover_local_pdfs(data_dir: Path) -> List[Path]:
    pdf_dir = data_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    return sorted(pdf_dir.glob("*.pdf"))
