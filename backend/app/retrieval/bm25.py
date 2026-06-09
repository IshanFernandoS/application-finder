from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Tuple

TOKEN_RE = re.compile(r"[A-Za-z0-9_./+-]+")


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class BM25Index:
    def __init__(self, documents: Iterable[Tuple[str, str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_ids: List[str] = []
        self.doc_lens: Dict[str, int] = {}
        self.term_freqs: Dict[str, Counter] = {}
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        for doc_id, text in documents:
            tokens = tokenize(text)
            counts = Counter(tokens)
            self.doc_ids.append(doc_id)
            self.doc_lens[doc_id] = len(tokens)
            self.term_freqs[doc_id] = counts
            for term in counts:
                self.doc_freqs[term] += 1
        self.avgdl = sum(self.doc_lens.values()) / max(len(self.doc_lens), 1)

    def score(self, query: str, doc_id: str) -> float:
        tokens = tokenize(query)
        n_docs = max(len(self.doc_ids), 1)
        score = 0.0
        doc_len = self.doc_lens.get(doc_id, 0)
        counts = self.term_freqs.get(doc_id, Counter())
        for term in tokens:
            freq = counts.get(term, 0)
            if not freq:
                continue
            df = self.doc_freqs.get(term, 0)
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            denom = freq + self.k1 * (1 - self.b + self.b * doc_len / max(self.avgdl, 1e-9))
            score += idf * (freq * (self.k1 + 1)) / denom
        return float(score)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        scored = [(doc_id, self.score(query, doc_id)) for doc_id in self.doc_ids]
        scored.sort(key=lambda item: item[1], reverse=True)
        return [(doc_id, score) for doc_id, score in scored[:top_k] if score > 0]
