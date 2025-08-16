# annotator/app.py

import pandas as pd
import ipywidgets as widgets
from IPython.display import display, clear_output
from ipyfilechooser import FileChooser
import os
from .image_processing import process_cell_type_map
from .editor import CellTypeAnnotator
import matplotlib.pyplot as plt

class AnnotationApp:
    """
    一个多模式、带高级参数、美化过的、用于启动 CellTypeAnnotator 的应用封装 (最终美化版)
    """
    def __init__(self, start_path: str = '.'):
        # --- 定义通用布局样式 ---
        self.box_layout = widgets.Layout(border='1px solid #DDDDDD', padding='10px', margin='5px 0', border_radius='5px')
        fc_layout = widgets.Layout(width='98%', height='280px') # FileChooser 宽度设为98%以适应VBox

        def _create_mapping_ui(show_type=False, show_barcode=True):
            widgets_list = []; dd_map = {}
            if show_barcode:
                dd_map['barcode'] = widgets.Dropdown(description="Barcode 列:")
                widgets_list.append(dd_map['barcode'])
            dd_map['x'] = widgets.Dropdown(description="X坐标列:"); dd_map['y'] = widgets.Dropdown(description="Y坐标列:")
            widgets_list.extend([dd_map['x'], dd_map['y']])
            if show_type:
                dd_map['type'] = widgets.Dropdown(description="类型列:")
                widgets_list.append(dd_map['type'])
            
            # 为匹配框增加边框和内边距
            mapping_box = widgets.VBox(widgets_list, layout=self.box_layout)
            # 初始隐藏，需要时再显示
            mapping_box.layout.display = 'none' 
            return mapping_box, dd_map

        # --- Tab 1: 从图像生成 ---
        tab1_fc_box = widgets.HBox([
            widgets.VBox([widgets.HTML("<b>步骤 1: 选择图像文件</b>"), FileChooser(start_path, layout=fc_layout, filter_pattern=['*.tif','*.tiff','*.jpg','*.jpeg','*.png'])], layout=widgets.Layout(width='50%')),
            widgets.VBox([widgets.HTML("<b>步骤 2: 选择坐标 CSV (可选)</b>"), FileChooser(start_path, layout=fc_layout, filter_pattern=['*.csv'])], layout=widgets.Layout(width='50%'))
        ])
        self.image_chooser = tab1_fc_box.children[0].children[1]
        self.barcode_chooser_img = tab1_fc_box.children[1].children[1]
        
        self.img_mapping_box, self.img_dd_map = _create_mapping_ui()
        self.n_types_input = widgets.IntText(value=6, description='目标类别数:', style={'description_width': 'initial'})
        self.grid_width_input = widgets.IntText(value=50, description='网格宽度:', style={'description_width': 'initial'}); self.grid_height_input = widgets.IntText(value=50, description='网格高度:', style={'description_width': 'initial'}); self.remove_background_checkbox = widgets.Checkbox(value=True, description='移除背景区域'); self.background_color_input = widgets.Text(value='(255, 255, 255)', description='背景色 (R,G,B):', style={'description_width': 'initial'}); self.correct_black_checkbox = widgets.Checkbox(value=True, description='修正近黑区域'); self.black_threshold_input = widgets.IntText(value=60, description='近黑阈值 (R+G+B <):', style={'description_width': 'initial'})
        adv_settings = widgets.VBox([widgets.HBox([self.grid_width_input, self.grid_height_input]), widgets.HBox([self.remove_background_checkbox, self.background_color_input]), widgets.HBox([self.correct_black_checkbox, self.black_threshold_input])])
        self.adv_accordion = widgets.Accordion(children=[adv_settings]); self.adv_accordion.set_title(0, '高级参数设置')
        self.generate_button = widgets.Button(description='从图像生成并编辑', button_style='success', icon='cogs', layout=widgets.Layout(width='99%'))
        
        # 将列匹配框放在其父控件下方
        tab1_fc_box.children[1].children = (*tab1_fc_box.children[1].children, self.img_mapping_box)
        
        tab1_settings_box = widgets.Box([widgets.VBox([widgets.HTML("<b>步骤 3: 设置参数</b>"), self.n_types_input, self.adv_accordion])], layout=self.box_layout)
        tab1_content = widgets.VBox([tab1_fc_box, tab1_settings_box, self.generate_button])

        # --- Tab 2: 加载已有标注 ---
        self.existing_csv_chooser = FileChooser(start_path, title='<b>步骤 1: 选择已有的标注CSV文件</b>', layout=fc_layout)
        self.existing_csv_chooser.filter_pattern = ['*.csv']
        self.barcode_chooser_load = FileChooser(start_path, title='<b>步骤 2: 选择官方坐标 CSV (可选)</b>', layout=fc_layout)
        self.barcode_chooser_load.filter_pattern = ['*.csv']
        self.existing_mapping_box, self.existing_dd_map = _create_mapping_ui(show_type=True, show_barcode=True)
        self.load_coords_mapping_box, self.load_coords_dd_map = _create_mapping_ui(show_barcode=True)
        self.start_editing_button = widgets.Button(description='开始编辑', icon='pencil', button_style='success', layout=widgets.Layout(width='99%'))
        
        tab2_content = widgets.VBox([
            widgets.HBox([
                widgets.VBox([self.existing_csv_chooser, self.existing_mapping_box]),
                widgets.VBox([self.barcode_chooser_load, self.load_coords_mapping_box])
            ]),
            self.start_editing_button
        ])

        # --- Tab 3: 创建空白画布 ---
        self.blank_width_input = widgets.IntText(value=50, description='画布宽度 (spots):'); self.blank_height_input = widgets.IntText(value=50, description='画布高度 (spots):')
        self.barcode_chooser_blank = FileChooser(start_path, title='步骤 2: 选择坐标文件 (可选)', layout=fc_layout)
        self.barcode_chooser_blank.filter_pattern = ['*.csv']
        self.blank_mapping_box, self.blank_dd_map = _create_mapping_ui()
        self.create_blank_button = widgets.Button(description='创建空白画布并编辑', button_style='info', icon='square-o', layout=widgets.Layout(width='99%'))
        
        blank_settings_box = widgets.VBox([widgets.HTML("<b>步骤 1: 设置画布尺寸</b>"), self.blank_width_input, self.blank_height_input], layout=self.box_layout)
        blank_chooser_box = widgets.VBox([self.barcode_chooser_blank, self.blank_mapping_box], layout=widgets.Layout(flex='1', margin='0 0 0 10px'))
        tab3_content = widgets.VBox([widgets.HBox([blank_settings_box, blank_chooser_box]), self.create_blank_button])
        
        self.tab_widget = widgets.Tab(children=[tab1_content, tab2_content, tab3_content]); self.tab_widget.set_title(0, '从图像生成'); self.tab_widget.set_title(1, '加载已有标注'); self.tab_widget.set_title(2, '创建空白画布')
        self.tool_container = widgets.Output(); self.app_layout = widgets.VBox([widgets.HTML("<h1>多功能空间注释平台</h1><hr>"), self.tab_widget, self.tool_container])
        
        # 绑定事件
        self.barcode_chooser_img.register_callback(lambda chooser: self._populate_mappers(chooser, self.img_mapping_box, self.img_dd_map))
        self.existing_csv_chooser.register_callback(lambda chooser: self._populate_mappers(chooser, self.existing_mapping_box, self.existing_dd_map))
        self.barcode_chooser_load.register_callback(lambda chooser: self._populate_mappers(chooser, self.load_coords_mapping_box, self.load_coords_dd_map))
        self.barcode_chooser_blank.register_callback(lambda chooser: self._populate_mappers(chooser, self.blank_mapping_box, self.blank_dd_map))
        self.generate_button.on_click(self._on_generate_click); self.start_editing_button.on_click(self._on_start_editing_click); self.create_blank_button.on_click(self._on_create_blank_click)

    # (所有 _populate_mappers, _rename_df_cols 和 _on_click 等核心逻辑函数都保持不变)
    def _populate_mappers(self, chooser, mapping_box, dd_map):
        path = chooser.selected; mapping_box.layout.display = 'none'
        if path and os.path.exists(path):
            try:
                cols = pd.read_csv(path, nrows=0).columns.tolist(); guesses = self._guess_column_names(cols)
                for name, dd in dd_map.items():
                    dd.options = cols
                    if name in guesses: dd.value = guesses[name]
                mapping_box.layout.display = 'block'
            except Exception as e: print(f"无法读取CSV文件: {e}")
    def _guess_column_names(self, columns):
        guesses = {}; cols_lower = {c.lower(): c for c in columns}
        patterns = {'barcode': ['barcode', 'barcodes', 'cell_id'], 'x': ['x', 'x_coord', 'grid_x', 'array_col', 'x_coordinate'], 'y': ['y', 'y_coord', 'grid_y', 'array_row', 'y_coordinate'], 'type': ['type', 'cell_type', 'label', 'annotation', 'cluster']}
        for key, p_list in patterns.items():
            for p in p_list:
                if p in cols_lower: guesses[key] = cols_lower[p]; break
        return guesses
    def _rename_df_cols(self, df, dd_map):
        rename_map = {}
        if 'barcode' in dd_map and dd_map['barcode'].value: rename_map[dd_map['barcode'].value] = 'barcode'
        if 'x' in dd_map and dd_map['x'].value: rename_map[dd_map['x'].value] = 'grid_x'
        if 'y' in dd_map and dd_map['y'].value: rename_map[dd_map['y'].value] = 'grid_y'
        if 'type' in dd_map and dd_map['type'].value: rename_map[dd_map['type'].value] = 'cell_type'
        return df.rename(columns=rename_map)
    def _on_generate_click(self, b):
        self.tool_container.clear_output(wait=True)
        with self.tool_container:
            img_path = self.image_chooser.selected; barcode_path = self.barcode_chooser_img.selected
            if not img_path or not os.path.exists(img_path): print("错误：请选择一个有效的图像文件。"); return
            grid_w = self.grid_width_input.value; grid_h = self.grid_height_input.value
            if barcode_path and os.path.exists(barcode_path):
                spatial_df = pd.read_csv(barcode_path); spatial_df = self._rename_df_cols(spatial_df, self.img_dd_map)
                if 'barcode' not in spatial_df.columns: print("警告：坐标文件中缺少barcode列。"); spatial_df['barcode'] = [f"spot_{r.grid_y}_{r.grid_x}" for r in spatial_df.itertuples()]
            else:
                print("提示：未提供坐标CSV，将自动生成占位符barcodes。")
                barcodes = [f"spot_{y}_{x}" for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)]; x_coords = [x for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)]; y_coords = [y for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)]
                spatial_df = pd.DataFrame({'barcode': barcodes, 'x_coord': x_coords, 'y_coord': y_coords})
            spatial_df.rename(columns={'grid_x': 'x_coord', 'grid_y': 'y_coord'}, inplace=True)
            params = {'grid_width': grid_w, 'grid_height': grid_h, 'n_types': self.n_types_input.value, 'correct_near_black': self.correct_black_checkbox.value, 'near_black_threshold': self.black_threshold_input.value, 'remove_background': self.remove_background_checkbox.value, 'background_color_str': self.background_color_input.value}
            auto_annotations_df = process_cell_type_map(img_path, spatial_df, **params)
            if not auto_annotations_df.empty:
                print("\n--- 自动注释完成！正在启动交互式编辑器... ---")
                annotator = CellTypeAnnotator(annotation_df=auto_annotations_df); display(annotator.get_layout())
            else: print("\n错误：自动注释过程未能生成任何结果。")
    def _on_start_editing_click(self, b):
        self.tool_container.clear_output(wait=True)
        with self.tool_container:
            csv_path = self.existing_csv_chooser.selected
            if not csv_path or not os.path.exists(csv_path): print("错误：请选择一个有效的主标注文件。"); return
            df = pd.read_csv(csv_path)
            df = self._rename_df_cols(df, self.existing_dd_map)
            if 'barcode' not in df.columns: df['barcode'] = [f"spot_{r.grid_y}_{r.grid_x}" for r in df.itertuples()]
            if 'color' not in df.columns: df['color'] = [(128, 128, 128)] * len(df)
            master_coords_df = None
            barcode_path = self.barcode_chooser_load.selected
            if barcode_path and os.path.exists(barcode_path):
                print("--- 正在加载官方坐标文件用于Barcode重命名... ---")
                master_coords_df = pd.read_csv(barcode_path); master_coords_df = self._rename_df_cols(master_coords_df, self.load_coords_dd_map)
            print("\n--- 文件加载成功！正在启动交互式编辑器... ---")
            annotator = CellTypeAnnotator(annotation_df=df, master_coordinate_df=master_coords_df)
            display(annotator.get_layout())
    def _on_create_blank_click(self, b):
        self.tool_container.clear_output(wait=True)
        with self.tool_container:
            grid_w = self.blank_width_input.value; grid_h = self.blank_height_input.value
            df = pd.DataFrame({'grid_x': [x for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)], 'grid_y': [y for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)], 'cell_type': 'Unassigned', 'color': [(255, 255, 255)] * (grid_w * grid_h)})
            master_coords_df = None
            barcode_path = self.barcode_chooser_blank.selected
            if barcode_path and os.path.exists(barcode_path):
                print("--- 正在加载官方坐标文件用于提供Barcode... ---")
                master_coords_df = pd.read_csv(barcode_path); master_coords_df = self._rename_df_cols(master_coords_df, self.blank_dd_map)
            if master_coords_df is not None and 'barcode' in master_coords_df.columns:
                df = pd.merge(df.drop(columns=['barcode'], errors='ignore'), master_coords_df[['grid_x', 'grid_y', 'barcode']], on=['grid_x', 'grid_y'], how='left')
            if 'barcode' not in df.columns: df['barcode'] = [f"spot_{r.grid_y}_{r.grid_x}" for r in df.itertuples()]
            unmatched_mask = df['barcode'].isnull()
            if unmatched_mask.any():
                new_barcodes = [f"spot_{r.grid_y}_{r.grid_x}" for r in df[unmatched_mask].itertuples()]
                df.loc[unmatched_mask, 'barcode'] = new_barcodes
            print("\n--- 空白画布创建成功！正在启动交互式编辑器... ---")
            annotator = CellTypeAnnotator(annotation_df=df, master_coordinate_df=master_coords_df)
            display(annotator.get_layout())
    
    def display_app(self):
        display(self.app_layout)
