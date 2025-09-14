# fastgi/config.py
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np

@dataclass
class PlyConfig:
    """Configuration for reading PLY files."""
    color_props: List[str] = field(default_factory=lambda: ["red", "green", "blue"])
    pos_props: List[str] = field(default_factory=lambda: ["x", "y", "z"])
    auto_detect: bool = True

@dataclass
class FitConfig:
    """Configuration for the fitting process."""
    max_points_in_cluster: int = 32
    color_homogeneity_threshold: float = 0.2
    use_gmm: bool = True
    gmm_max_components: int = 2
    gmm_points_per_component: int = 8
    gmm_covariance_type: str = "full" # "full", "diag", "tied", "spherical"
    scale_modifier: float = 1.5
    opacity_modifier: float = 0.6

@dataclass
class RenderConfig:
    """Configuration for rendering."""
    resolution: Tuple[int, int] = (512, 512)
    fov_degrees: float = 60.0
    camera_pos: Optional[np.ndarray] = None
    look_at: Optional[np.ndarray] = None
    view_at_center: bool = True
    bg_color: Tuple[float, float, float] = (0.1, 0.1, 0.1) # 0-1 float
    near_plane: float = 0.1