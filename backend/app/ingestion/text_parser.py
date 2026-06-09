from __future__ import annotations

from pathlib import Path
from typing import List, Tuple


def parse_text_file(path: Path) -> List[Tuple[int, str, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    chunks: List[Tuple[int, str, str]] = []
    section = path.stem
    buffer: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if buffer:
                chunks.append((1, section, "\n".join(buffer).strip()))
                buffer = []
            section = stripped.lstrip("#").strip() or section
        else:
            buffer.append(line)
    if buffer:
        chunks.append((1, section, "\n".join(buffer).strip()))
    return [(page, sec, body) for page, sec, body in chunks if body]
