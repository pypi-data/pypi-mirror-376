# fastgi/__init__.py

"""
fastgi - Fast Gaussian Initialization

A library for fast CPU-based initialization of 3D Gaussian Splatting models.
"""


from .config import PlyConfig, FitConfig, RenderConfig
from .io import PlyFile, save_gaussians 
from .core import Fit
from .viz import view_ply

__version__ = "0.1.0"