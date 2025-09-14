# fastgi/viz.py
import os
import numpy as np

try:
    import open3d as o3d
    _have_o3d = True
except ImportError:
    _have_o3d = False

def view_ply(path: str, window_size: tuple[int, int] = (400, 400)):
    """
    Displays a PLY file using Open3D with a specified window size.
    
    Args:
        path (str): The path to the PLY file.
        window_size (tuple[int, int]): The desired width and height of the visualization window.
    """
    if not _have_o3d:
        print("Open3D is not installed. Please install it with 'pip install open3d'")
        return
    
    if not os.path.exists(path):
        print(f"Error: File not found at {path}")
        return
        
    print(f"Visualizing {path} with Open3D...")
    pcd = o3d.io.read_point_cloud(path)
    if not pcd.has_points():
        print("Warning: The PLY file contains no points.")
        return
    
    # --- Настройка размера окна ---
    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="FastGI PLY Viewer", width=window_size[0], height=window_size[1])
    vis.add_geometry(pcd)
    opt = vis.get_render_option()
    opt.point_size = 2.0
    opt.background_color = np.array([0.06, 0.06, 0.08])

    opt.show_coordinate_frame = True  # можно оставить или убрать
    ctr = vis.get_view_control()
    ctr.set_zoom(0.8) 

    print(f"Window size set to {window_size[0]}x{window_size[1]}. Press 'Q' to close.")
    vis.run()
    vis.destroy_window()