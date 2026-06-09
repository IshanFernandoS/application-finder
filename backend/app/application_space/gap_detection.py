from __future__ import annotations

from typing import List, Tuple

import numpy as np
from sklearn.neighbors import NearestNeighbors


def candidate_gap_points(coords: np.ndarray, cluster_labels: np.ndarray, max_points: int = 12) -> List[Tuple[List[float], List[int]]]:
    if len(coords) < 3:
        return []
    labels = sorted(set(int(label) for label in cluster_labels if int(label) >= 0))
    candidates: List[Tuple[List[float], List[int]]] = []
    centroids = []
    for label in labels:
        members = coords[cluster_labels == label]
        if len(members):
            centroids.append((label, members.mean(axis=0)))
    for i, (label_a, center_a) in enumerate(centroids):
        for label_b, center_b in centroids[i + 1 :]:
            midpoint = (center_a + center_b) / 2.0
            candidates.append((midpoint.tolist(), [label_a, label_b]))
    if not candidates:
        nbrs = NearestNeighbors(n_neighbors=min(3, len(coords))).fit(coords)
        distances, indices = nbrs.kneighbors(coords)
        order = np.argsort(distances[:, -1])[::-1]
        for idx in order[:max_points]:
            candidates.append((coords[idx].tolist(), [int(cluster_labels[i]) for i in indices[idx]]))
    return candidates[:max_points]
