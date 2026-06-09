from __future__ import annotations

from typing import List

import numpy as np
from sklearn.neighbors import NearestNeighbors


def inverse_density(coords: np.ndarray, k: int = 5) -> List[float]:
    if len(coords) < 2:
        return [0.0 for _ in coords]
    n = min(k, len(coords) - 1)
    nbrs = NearestNeighbors(n_neighbors=n + 1).fit(coords)
    distances, _ = nbrs.kneighbors(coords)
    kth = distances[:, -1]
    max_dist = float(kth.max()) or 1.0
    return [float(value / max_dist) for value in kth]
