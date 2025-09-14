# fastgi/io.py

import numpy as np
from plyfile import PlyData, PlyElement
from typing import Tuple, Optional

from .config import PlyConfig

class PlyFile:
    """Represents a point cloud read from a PLY file or creates a default black cloud."""
    def __init__(self, path: Optional[str] = None, config: Optional['PlyConfig'] = None, 
                 default_points: int = 1000):
        self.path = path
        self.config = config if config is not None else PlyConfig()
        self.points: np.ndarray = np.array([])
        self.colors: np.ndarray = np.array([])

        if path is not None:
            try:
                self._load()
            except (IOError, ValueError) as e:
                print(f"Failed to load PLY file '{path}': {e}")
                print("Creating default black point cloud at origin.")
                self._create_default(default_points)
        else:
            # No path provided → create default
            self._create_default(default_points)

    def _load(self):
        """Flexible PLY reader."""
        plydata = PlyData.read(self.path)

        for element in plydata.elements:
            if 'vertex' not in element.name:
                continue

            props = {p.name.lower() for p in element.properties}
            pos_props = {p.lower() for p in self.config.pos_props}
            
            if pos_props.issubset(props):
                # Found positions
                self.points = np.vstack([element.data[p] for p in self.config.pos_props]).T.astype(np.float32)
                
                # Try to find colors
                color_props_lower = {p.lower() for p in self.config.color_props}
                if color_props_lower.issubset(props):
                    colors_raw = np.vstack([element.data[p] for p in self.config.color_props]).T.astype(np.float32)
                    if np.max(colors_raw) > 1.0:
                        colors_raw /= 255.0
                    self.colors = np.clip(colors_raw, 0.0, 1.0)
                else:
                    self.colors = np.full_like(self.points, 0.0, dtype=np.float32)  # black
                print(f"Loaded {len(self.points)} points from {self.path}")
                return
        
        raise ValueError("Could not find a vertex element with position properties in the PLY file.")

    def _create_default(self, n_points: int):
        """Creates a point cloud with all points at origin and black color."""
        self.points = np.zeros((n_points, 3), dtype=np.float32)
        self.colors = np.zeros_like(self.points, dtype=np.float32)  # black
        print(f"Created default black point cloud with {n_points} points at origin.")

def _sh_from_rgb(rgb):
    """Converts RGB to spherical harmonics DC component."""
    C0 = 0.28209479177387814
    return (rgb - 0.5) / C0

def save_gaussians(path: str, gaussians: dict):
    """Saves Gaussian data to a PLY file in the standard 3DGS format."""
    positions = gaussians.get("positions", np.array([]))
    if positions.shape[0] == 0:
        print("Warning: No Gaussians to save.")
        return

    # Prepare attributes
    scales = np.exp(gaussians.get("scales", np.zeros_like(positions)))
    quats = gaussians.get("quaternions", np.tile([1.0, 0.0, 0.0, 0.0], (len(positions), 1)))
    
    # Ensure quaternion is (w, x, y, z) and normalized
    if quats.shape[1] == 4:
       quats = quats / np.linalg.norm(quats, axis=1, keepdims=True)

    # Convert RGB to spherical harmonics DC component
    colors = gaussians.get("colors", np.zeros_like(positions))
    shs = _sh_from_rgb(colors)
    
    # Convert opacity to logit space
    opacities = gaussians.get("opacities", np.zeros(len(positions)))
    opacities_logit = np.log(opacities / (1 - opacities))

    # Define the vertex element structure
    vertex_dtype = [
        ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
        ('nx', 'f4'), ('ny', 'f4'), ('nz', 'f4'),
        ('f_dc_0', 'f4'), ('f_dc_1', 'f4'), ('f_dc_2', 'f4'),
        ('f_rest_0', 'f4'), ('f_rest_1', 'f4'), ('f_rest_2', 'f4'), ('f_rest_3', 'f4'),
        ('f_rest_4', 'f4'), ('f_rest_5', 'f4'), ('f_rest_6', 'f4'), ('f_rest_7', 'f4'),
        ('f_rest_8', 'f4'), ('f_rest_9', 'f4'), ('f_rest_10', 'f4'), ('f_rest_11', 'f4'),
        ('opacity', 'f4'),
        ('scale_0', 'f4'), ('scale_1', 'f4'), ('scale_2', 'f4'),
        ('rot_0', 'f4'), ('rot_1', 'f4'), ('rot_2', 'f4'), ('rot_3', 'f4')
    ]
    
    num_vertices = len(positions)
    vertices = np.zeros(num_vertices, dtype=vertex_dtype)
    
    # Fill the structured array
    attrs = {
        'x': positions[:, 0], 'y': positions[:, 1], 'z': positions[:, 2],
        'nx': np.zeros(num_vertices), 'ny': np.zeros(num_vertices), 'nz': np.zeros(num_vertices),
        'f_dc_0': shs[:, 0], 'f_dc_1': shs[:, 1], 'f_dc_2': shs[:, 2],
        'opacity': opacities_logit,
        'scale_0': scales[:, 0], 'scale_1': scales[:, 1], 'scale_2': scales[:, 2],
        'rot_0': quats[:, 0], 'rot_1': quats[:, 1], 'rot_2': quats[:, 2], 'rot_3': quats[:, 3]
    }
    for name, data in attrs.items():
        vertices[name] = data

    # Create PlyElement and PlyData, then write to file
    vertex_element = PlyElement.describe(vertices, 'vertex')
    ply_data = PlyData([vertex_element], text=False)
    ply_data.write(path)
    print(f"Saved {num_vertices} Gaussians to {path}")

