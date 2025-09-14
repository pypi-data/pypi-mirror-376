# fastgi/render.py

import numpy as np
from scipy.spatial.transform import Rotation as R
from tqdm import tqdm
import math

from .config import RenderConfig


def render_gaussians(gaussians: dict, config: RenderConfig) -> np.ndarray:
    """
    Renders an image from a dictionary of Gaussian data based on a RenderConfig.

    Args:
        gaussians (dict): A dictionary containing 'positions', 'scales', 'quaternions', etc.
        config (RenderConfig): The configuration object for rendering settings.

    Returns:
        np.ndarray: The rendered image as a NumPy array (H, W, 3) in uint8 format.
    """
    

    positions = gaussians["positions"].astype(np.float32)
    scales = np.exp(gaussians["scales"].astype(np.float32)) # Convert log-scales to scales
    quats = gaussians["quaternions"].astype(np.float32)
    colors = gaussians["colors"].astype(np.float32)
    opacities = gaussians["opacities"].astype(np.float32)

    W, H = config.resolution
    BG_COLOR = np.array(config.bg_color) * 255.0 # Convert 0-1 color to 0-255

    def setup_camera(cam_pos, target_pos):
        forward = target_pos - cam_pos
        forward_norm = np.linalg.norm(forward)
        forward = forward / (forward_norm + 1e-9)
        
        world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        if np.abs(np.dot(forward, world_up)) > 0.999:
            world_up = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            
        right = np.cross(world_up, forward)
        right /= (np.linalg.norm(right) + 1e-12)
        up = np.cross(forward, right)
        
        return np.vstack([right, up, forward]).astype(np.float32)

    if config.view_at_center or config.camera_pos is None:
        target_pos = np.mean(positions, axis=0) if len(positions) > 0 else np.array([0.0, 0.0, 0.0])
        
        bounding_radius = np.max(np.linalg.norm(positions - target_pos, axis=1)) if len(positions) > 0 else 1.0
        fov_rad = np.radians(config.fov_degrees)
        distance = bounding_radius / (np.tan(fov_rad / 2) + 1e-12) * 1.8 # Multiplier for padding
        
        # A default view direction if none specified
        view_dir = np.array([0.5, -0.5, 1.0], dtype=np.float32) 
        view_dir /= np.linalg.norm(view_dir)
        
        cam_pos = target_pos + view_dir * distance
    else:
        cam_pos = config.camera_pos
        target_pos = config.look_at if config.look_at is not None else np.mean(positions, axis=0)

    R_cam = setup_camera(cam_pos, target_pos)

    cam_coords = (positions - cam_pos) @ R_cam.T
    depth_order = np.argsort(cam_coords[:, 2])[::-1]

    canvas_rgb = np.full((H, W, 3), BG_COLOR, dtype=np.float32)

    aspect_ratio = W / H
    focal_y = H / (2.0 * np.tan(np.radians(config.fov_degrees) / 2.0))
    focal_x = focal_y * aspect_ratio

    for i in tqdm(depth_order, desc="Rendering image", leave=False):
        pos_cam = cam_coords[i]
        z = pos_cam[2]
        if z <= config.near_plane:
            continue

        q_raw = quats[i]
        # Scipy expects (x, y, z, w), but many systems use (w, x, y, z).
        # Heuristic: if first element's abs value is large, it's probably w.
        if abs(q_raw[0]) > abs(q_raw[3]):
            q_scipy = np.array([q_raw[1], q_raw[2], q_raw[3], q_raw[0]])
        else:
            q_scipy = q_raw
        
        R_obj = R.from_quat(q_scipy / (np.linalg.norm(q_scipy) + 1e-9)).as_matrix()
        
        S = np.diag(scales[i])
        Sigma_world = R_obj @ S @ S.T @ R_obj.T
        Sigma_cam = R_cam @ Sigma_world @ R_cam.T
        
        J = np.array([
            [focal_x / z, 0.0, -focal_x * pos_cam[0] / (z * z)],
            [0.0, focal_y / z, -focal_y * pos_cam[1] / (z * z)]
        ], dtype=np.float32)

        cov_2d = J @ Sigma_cam @ J.T
        
        try:
            vals, vecs = np.linalg.eigh(cov_2d)
        except np.linalg.LinAlgError as e:
            import warnings
            warnings.warn(f"np.linalg.LinAlgError: {e}")
            continue
            
        vals = np.maximum(vals, 1e-8)
        sigma_x, sigma_y = np.sqrt(vals[1]), np.sqrt(vals[0])
        rot = vecs
        
        center_x = focal_x * pos_cam[0] / z + W * 0.5
        center_y = focal_y * pos_cam[1] / z + H * 0.5
        
        radius_px = int(math.ceil(3.0 * max(sigma_x, sigma_y)))
        xmin, xmax = max(0, int(center_x - radius_px)), min(W, int(center_x + radius_px))
        ymin, ymax = max(0, int(center_y - radius_px)), min(H, int(center_y + radius_px))
        if xmin >= xmax or ymin >= ymax:
            continue

        px, py = np.meshgrid(np.arange(xmin, xmax), np.arange(ymin, ymax))
        px_centered, py_centered = px - center_x, py - center_y
        
        px_local = rot[0, 0] * px_centered + rot[1, 0] * py_centered
        py_local = rot[0, 1] * px_centered + rot[1, 1] * py_centered
        
        alpha_mask = np.exp(-0.5 * ((px_local / sigma_x)**2 + (py_local / sigma_y)**2))
        alpha = alpha_mask * opacities[i]
        
        splat_color = colors[i] * 255.0
        
        # Blending
        alpha = alpha[..., np.newaxis]
        current_color = canvas_rgb[ymin:ymax, xmin:xmax]
        canvas_rgb[ymin:ymax, xmin:xmax] = splat_color * alpha + current_color * (1 - alpha)

    return np.clip(canvas_rgb, 0, 255).astype(np.uint8)