from dataclasses import dataclass

import numpy as np

from yumo.constants import CMAPS


# --- Context ---
@dataclass
class Context:
    # Data
    points: np.ndarray = None  # type: ignore[assignment]
    mesh_vertices: np.ndarray | None = None
    mesh_faces: np.ndarray | None = None

    # Statistics
    min_value: float = None  # type: ignore[assignment]
    max_value: float = None  # type: ignore[assignment]

    center: np.ndarray = None  # type: ignore[assignment]
    bbox_min: np.ndarray = None  # type: ignore[assignment]
    bbox_max: np.ndarray = None  # type: ignore[assignment]

    points_densest_distance: float = None  # type: ignore[assignment]

    # Settings
    cmap: str = CMAPS[0]
    color_min: float = None  # type: ignore[assignment]
    color_max: float = None  # type: ignore[assignment]
