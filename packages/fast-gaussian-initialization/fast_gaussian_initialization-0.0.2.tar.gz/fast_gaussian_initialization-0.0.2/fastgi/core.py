# fastgi/core.py

import numpy as np
from scipy.spatial import KDTree
from scipy.spatial.transform import Rotation as R
from collections import deque
from typing import List, Optional
from tqdm import tqdm

try:
    from sklearn.mixture import GaussianMixture
    _have_sklearn = True
except ImportError:
    _have_sklearn = False

from .config import FitConfig
from .io import PlyFile, save_gaussians
from .render import render_gaussians
from .config import RenderConfig

class Fit:
    """
    Fits 3D Gaussians to a point cloud from a PlyFile.
    """
    def __init__(self, ply_file: PlyFile, config: Optional[FitConfig] = None):
        self.ply_file = ply_file
        self.config = config if config is not None else FitConfig()
        self.gaussians = {}
        
        if self.ply_file.points.shape[0] > 0:
            self._run_pipeline()

    def _cluster_greedy(self) -> List[np.ndarray]:
        """Greedy region growing with KDTree and color distance threshold."""
        coords = self.ply_file.points
        colors = self.ply_file.colors
        n_limit = self.config.max_points_in_cluster
        s_threshold = self.config.color_homogeneity_threshold
        
        N = coords.shape[0]
        assigned = np.zeros(N, dtype=bool)
        kdt = KDTree(coords)
        clusters: List[np.ndarray] = []
        
        pbar = tqdm(total=N, desc="1/2 Clustering")
        while np.sum(assigned) < N:
            unassigned_indices = np.where(~assigned)[0]
            if len(unassigned_indices) == 0:
                break
            
            seed_idx = np.random.choice(unassigned_indices)
            
            cluster_indices = [seed_idx]
            assigned[seed_idx] = True
            
            seed_color = colors[seed_idx]
            
            candidates = deque()
            # Find initial neighbors for the seed
            _, neighs = kdt.query(coords[seed_idx], k=min(n_limit, N - 1))
            for n in np.atleast_1d(neighs):
                if not assigned[n]:
                    candidates.append(n)
            
            while candidates and len(cluster_indices) < n_limit:
                cand_idx = candidates.popleft()
                if assigned[cand_idx]:
                    continue
                
                # Check color homogeneity
                if np.linalg.norm(colors[cand_idx] - seed_color) < s_threshold:
                    assigned[cand_idx] = True
                    cluster_indices.append(cand_idx)

                    # Add new neighbors
                    _, new_neighs = kdt.query(coords[cand_idx], k=16)
                    for n in np.atleast_1d(new_neighs):
                        if not assigned[n]:
                            candidates.append(n)
            
            clusters.append(np.array(cluster_indices, dtype=int))
            pbar.update(len(cluster_indices))
            
        pbar.close()
        print(f"Clustering complete. Found {len(clusters)} clusters.")
        return clusters

    def _run_pipeline(self):
        """Executes the full clustering and Gaussian fitting pipeline."""
        clusters = self._cluster_greedy()
        self.gaussians = self._gaussianize_clusters(clusters)

    def save(self, path: str):
        """Saves the fitted Gaussians to a PLY file."""
        if not self.gaussians:
            raise RuntimeError("No Gaussians have been fitted. Run the pipeline first.")
        save_gaussians(path, self.gaussians)
    
    def test_render(self, config: Optional[RenderConfig] = None) -> np.ndarray:
        """Renders a test image of the fitted Gaussians."""
        if not self.gaussians:
            raise RuntimeError("No Gaussians have been fitted. Run the pipeline first.")
        
        render_config = config if config is not None else RenderConfig()
        
        return render_gaussians(self.gaussians, render_config)

    def _gaussianize_clusters(self, clusters: List[np.ndarray]) -> dict:
        """
        Fit Gaussians within each cluster using GMM or PCA fallback.
        """
        coords = self.ply_file.points
        colors = self.ply_file.colors
        
        gauss_positions = []
        gauss_scales = []
        gauss_quats = []
        gauss_colors = []
        raw_densities = []

        for indices in tqdm(clusters, desc="2/2 Gaussianizing"):
            if len(indices) < 4:
                continue

            points_in_cluster = coords[indices]
            colors_in_cluster = colors[indices]

            use_gmm = self.config.use_gmm and _have_sklearn
            gmm = None
            if use_gmm:
                try:
                    n_components = min(
                        self.config.gmm_max_components,
                        max(1, len(indices) // self.config.gmm_points_per_component),
                        len(indices)
                    )
                    gmm = GaussianMixture(
                        n_components=n_components,
                        covariance_type=self.config.gmm_covariance_type,
                        reg_covar=1e-6
                    )
                    gmm.fit(points_in_cluster)
                except Exception:
                    gmm = None

            if gmm is None:
                # PCA Fallback for one Gaussian
                position = np.mean(points_in_cluster, axis=0)
                points_centered = points_in_cluster - position
                covariance = np.cov(points_centered, rowvar=False)
                
                try:
                    eigvals, eigvecs = np.linalg.eigh(covariance)
                except np.linalg.LinAlgError:
                    continue

                order = np.argsort(eigvals)[::-1]
                eigvals = np.clip(eigvals[order], 1e-12, None)
                eigvecs = eigvecs[:, order]
                
                scales = np.sqrt(eigvals)
                if np.linalg.det(eigvecs) < 0:
                    eigvecs[:, -1] *= -1
                
                quat = R.from_matrix(eigvecs).as_quat()[[3, 0, 1, 2]] # w,x,y,z
                
                gauss_positions.append(position)
                gauss_scales.append(scales)
                gauss_quats.append(quat)
                gauss_colors.append(np.mean(colors_in_cluster, axis=0))
                raw_densities.append(len(indices) / (np.prod(scales) + 1e-12))

            else: # GMM succeeded
                for i in range(gmm.n_components):
                    mean = gmm.means_[i]
                    cov = gmm.covariances_[i]
                    
                    try:
                        eigvals, eigvecs = np.linalg.eigh(cov)
                    except np.linalg.LinAlgError:
                        continue
                        
                    order = np.argsort(eigvals)[::-1]
                    eigvals = np.clip(eigvals[order], 1e-12, None)
                    eigvecs = eigvecs[:, order]
                    
                    scales = np.sqrt(eigvals)
                    if np.linalg.det(eigvecs) < 0:
                        eigvecs[:, -1] *= -1
                    
                    quat = R.from_matrix(eigvecs).as_quat()[[3, 0, 1, 2]]
                    
                    # Weighted color
                    weights = gmm.predict_proba(points_in_cluster)[:, i]
                    color = np.sum(colors_in_cluster * weights[:, None], axis=0) / (np.sum(weights) + 1e-12)
                    
                    gauss_positions.append(mean)
                    gauss_scales.append(scales)
                    gauss_quats.append(quat)
                    gauss_colors.append(color)
                    raw_densities.append((weights.sum()) / (np.prod(scales) + 1e-12))
        
        if not gauss_positions:
            return {}

        # Post-process opacities
        opacities = np.array(raw_densities)
        opacities = np.log1p(opacities)
        clip_val = np.percentile(opacities, 99)
        opacities = np.clip(opacities, 0, clip_val) / (clip_val + 1e-12)
        opacities = 1 / (1 + np.exp(-opacities * self.config.opacity_modifier))
        
        return {
            "positions": np.array(gauss_positions, dtype=np.float32),
            "scales": np.log(np.array(gauss_scales, dtype=np.float32) * self.config.scale_modifier),
            "quaternions": np.array(gauss_quats, dtype=np.float32),
            "colors": np.clip(np.array(gauss_colors, dtype=np.float32), 0, 1),
            "opacities": np.array(opacities, dtype=np.float32)
        }