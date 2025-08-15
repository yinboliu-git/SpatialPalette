# annotator/image_processing.py

import pandas as pd
import numpy as np
from PIL import Image
from collections import Counter
from sklearn.cluster import KMeans
import ast

def _get_valid_neighbors(y, x, grid_map, background_color, near_black_threshold, grid_height, grid_width):
    # (此函数无需修改)
    neighbors = []
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0: continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < grid_height and 0 <= nx < grid_width:
                neighbor_color = grid_map[ny, nx]
                if neighbor_color != background_color and sum(neighbor_color) >= near_black_threshold:
                    neighbors.append(neighbor_color)
    return neighbors

def process_cell_type_map(image_path: str, spatial_df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    # (此函数无需修改)
    grid_width = kwargs.get('grid_width', 50)
    grid_height = kwargs.get('grid_height', 50)
    n_types = kwargs.get('n_types', 6)
    correct_near_black = kwargs.get('correct_near_black', True)
    n_correction_laps = kwargs.get('n_correction_laps', 2)
    near_black_threshold = kwargs.get('near_black_threshold', 60)
    remove_background = kwargs.get('remove_background', True)
    background_color_str = kwargs.get('background_color_str', '(255, 255, 255)')

    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img)
    img_height, img_width, _ = img_array.shape
    background_color = ast.literal_eval(background_color_str)
    
    print(f"--- 步骤 A: 图像分析 (网格大小: {grid_height}x{grid_width}) ---")
    tile_height = img_height // grid_height; tile_width = img_width // grid_width
    grid_data = []
    for y_idx in range(grid_height):
        for x_idx in range(grid_width):
            y_start, y_end = y_idx * tile_height, (y_idx + 1) * tile_height; x_start, x_end = x_idx * tile_width, (x_idx + 1) * tile_width
            tile = img_array[y_start:y_end, x_start:x_end, :]; pixels = tile.reshape(-1, 3); pixels_list = [tuple(p) for p in pixels]
            most_common_color = Counter(pixels_list).most_common(1)[0][0] if pixels_list else background_color
            grid_data.append({"grid_x": x_idx + 1, "grid_y": y_idx + 1, "color": most_common_color})
    grid_df = pd.DataFrame(grid_data)

    print(f"--- 步骤 B: 使用 K-Means 将颜色聚类为 {n_types} 类... ---")
    unique_colors = np.array([list(c) for c in grid_df['color'].unique() if sum(c) >= near_black_threshold and c != background_color])
    if len(unique_colors) < n_types: n_types = len(unique_colors)
    kmeans = KMeans(n_clusters=n_types, random_state=42, n_init=10).fit(unique_colors) if n_types > 0 else None
    valid_df = grid_df.copy()
    if remove_background: valid_df = valid_df[valid_df['color'] != background_color].copy()
    if correct_near_black:
        print(f"--- 步骤 C: 进行邻里校正... ---")
        grid_map = np.empty((grid_height, grid_width), dtype=object)
        for _, row in grid_df.iterrows(): grid_map[row['grid_y']-1, row['grid_x']-1] = row['color']
        for lap in range(n_correction_laps):
            correction_count = 0; new_grid_map = grid_map.copy()
            for y in range(grid_height):
                for x in range(grid_width):
                    current_color = grid_map[y, x]
                    if current_color == background_color: continue
                    if sum(current_color) < near_black_threshold:
                        neighbors = _get_valid_neighbors(y, x, grid_map, background_color, near_black_threshold, grid_height, grid_width)
                        if neighbors: new_grid_map[y, x] = Counter(neighbors).most_common(1)[0][0]; correction_count += 1
            grid_map = new_grid_map
            if correction_count == 0 and lap > 0: break
        corrected_data = []
        for y in range(grid_height):
            for x in range(grid_width):
                color = grid_map[y, x]
                if not (remove_background and color == background_color): corrected_data.append({"grid_x": x + 1, "grid_y": y + 1, "color": color})
        valid_df = pd.DataFrame(corrected_data)
    print(f"--- 步骤 D: 映射细胞类型并合并 Barcode... ---")
    if kmeans:
        final_colors = np.array([list(c) for c in valid_df['color'].unique() if sum(c) >= near_black_threshold and c != background_color])
        if len(final_colors) > 0:
            final_labels = kmeans.predict(final_colors)
            final_color_map = {tuple(color): f"Type_{label+1}" for color, label in zip(final_colors, final_labels)}
            valid_df['cell_type'] = valid_df['color'].map(final_color_map)
    valid_df['cell_type'].fillna('Unassigned', inplace=True)
    spatial_df = spatial_df.astype({'x_coord': int, 'y_coord': int})
    final_df = pd.merge(spatial_df, valid_df, left_on=['x_coord', 'y_coord'], right_on=['grid_x', 'grid_y'], how='inner')
    return final_df[['barcode', 'x_coord', 'y_coord', 'cell_type', 'color']].rename(columns={'x_coord': 'grid_x', 'y_coord': 'grid_y'})