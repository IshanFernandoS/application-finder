from __future__ import annotations

from typing import Tuple

import numpy as np


def reduce_to_2d(matrix, random_seed: int = 42) -> Tuple[np.ndarray, str]:
    try:
        import umap  # type: ignore

        if matrix.shape[0] >= 5:
            reducer = umap.UMAP(n_components=2, random_state=random_seed, metric="cosine")
            return reducer.fit_transform(matrix), "umap"
    except Exception:
        pass

    from sklearn.decomposition import PCA

    dense = matrix.toarray() if hasattr(matrix, "toarray") else matrix
    if dense.shape[1] == 1:
        dense = np.hstack([dense, np.zeros((dense.shape[0], 1))])
    coords = PCA(n_components=2, random_state=random_seed).fit_transform(dense)
    return coords, "pca"
