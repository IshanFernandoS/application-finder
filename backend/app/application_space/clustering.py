from __future__ import annotations

from typing import Tuple

import numpy as np


def cluster_points(coords: np.ndarray, random_seed: int = 42) -> Tuple[np.ndarray, str]:
    if len(coords) == 0:
        return np.asarray([]), "none"
    try:
        import hdbscan  # type: ignore

        if len(coords) >= 8:
            labels = hdbscan.HDBSCAN(min_cluster_size=max(3, len(coords) // 8)).fit_predict(coords)
            return labels, "hdbscan"
    except Exception:
        pass

    from sklearn.cluster import KMeans

    n_clusters = max(1, min(8, int(np.sqrt(len(coords)))))
    labels = KMeans(n_clusters=n_clusters, n_init=10, random_state=random_seed).fit_predict(coords)
    return labels, "kmeans"
