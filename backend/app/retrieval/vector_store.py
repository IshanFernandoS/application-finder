from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np


class JsonVectorStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._vectors: Dict[str, List[float]] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                self._vectors[row["id"]] = row["vector"]

    def upsert_many(self, rows: Iterable[Tuple[str, List[float]]]) -> None:
        for item_id, vector in rows:
            self._vectors[item_id] = vector
        with self.path.open("w", encoding="utf-8") as handle:
            for item_id, vector in sorted(self._vectors.items()):
                handle.write(json.dumps({"id": item_id, "vector": vector}) + "\n")

    def search(self, query_vector: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        if not self._vectors:
            return []
        q = np.asarray(query_vector, dtype=float)
        q_norm = np.linalg.norm(q) or 1.0
        scored: List[Tuple[str, float]] = []
        for item_id, vector in self._vectors.items():
            v = np.asarray(vector, dtype=float)
            denom = (np.linalg.norm(v) or 1.0) * q_norm
            scored.append((item_id, float(np.dot(q, v) / denom)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]
