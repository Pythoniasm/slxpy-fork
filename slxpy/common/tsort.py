from typing import List

import numpy as np


def tsort(am: np.ndarray) -> List[int]:
    assert am.shape[0] == am.shape[1], f"Adjacency matrix must be square, but got shape {am.shape}"
    verts = am.shape[0]

    elements = []  # List that will contain the sorted elements
    s = np.zeros(verts, dtype=np.bool_)
    s[~am.any(axis=0)] = 1

    # Kahn's algorithm
    while True:
        nz = s.nonzero()[0]
        if nz.size == 0:
            break
        vert = nz[0]
        s[vert] = 0
        elements.append(vert)
        row: np.ndarray = am[vert, :]
        indices = row.nonzero()[0]
        row.fill(0)
        col: np.ndarray = am[:, indices]
        s[indices[~col.any(axis=0)]] = 1

    if np.any(am):
        raise ValueError("Adjacency matrix contains circular structure.")
    else:
        return elements
