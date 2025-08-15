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
    # (为简洁，此处省略 AnnotationApp 的代码, 它与上一版完全相同)
    def __init__(self, start_path: str = '.'):
        box_layout = widgets.Layout(border='1px solid #ccc', padding='10px', margin='5px 0'); fc_layout = widgets.Layout(width='49%', height='280px')
        self.image_chooser = FileChooser(start_path, title='<b>步骤 1: 选择图像文件</b>', layout=fc_layout); self.image_chooser.filter_pattern = ['*.tif', '*.tiff', '*.jpg', '*.jpeg', '*.png']
        self.barcode_chooser_img = FileChooser(start_path, title='<b>步骤 2: 选择坐标 CSV (可选)</b>', layout=fc_layout); self.barcode_chooser_img.filter_pattern = ['*.csv']
        self.img_x_map_dd = widgets.Dropdown(description="X坐标列:"); self.img_y_map_dd = widgets.Dropdown(description="Y坐标列:"); self.img_mapping_box = widgets.VBox([widgets.HTML("<b>匹配坐标列名:</b>"), self.img_x_map_dd, self.img_y_map_dd], visible=False, layout=widgets.Layout(margin='5px 0'))
        self.n_types_input = widgets.IntText(value=6, description='目标类别数:', style={'description_width': 'initial'}); self.grid_width_input = widgets.IntText(value=50, description='网格宽度:', style={'description_width': 'initial'}); self.grid_height_input = widgets.IntText(value=50, description='网格高度:', style={'description_width': 'initial'}); self.remove_background_checkbox = widgets.Checkbox(value=True, description='移除背景区域'); self.background_color_input = widgets.Text(value='(255, 255, 255)', description='背景色 (R,G,B):', style={'description_width': 'initial'}); self.correct_black_checkbox = widgets.Checkbox(value=True, description='修正近黑区域'); self.black_threshold_input = widgets.IntText(value=60, description='近黑阈值 (R+G+B <):', style={'description_width': 'initial'})
        adv_settings = widgets.VBox([widgets.HBox([self.grid_width_input, self.grid_height_input]), widgets.HBox([self.remove_background_checkbox, self.background_color_input]), widgets.HBox([self.correct_black_checkbox, self.black_threshold_input])])
        self.adv_accordion = widgets.Accordion(children=[adv_settings]); self.adv_accordion.set_title(0, '高级参数设置')
        self.generate_button = widgets.Button(description='从图像生成并编辑', button_style='success', icon='cogs', layout=widgets.Layout(width='99%'))
        tab1_content = widgets.VBox([widgets.HBox([self.image_chooser, self.barcode_chooser_img]), self.img_mapping_box, widgets.Box([widgets.VBox([self.n_types_input, self.adv_accordion])], layout=box_layout), self.generate_button])
        self.existing_csv_chooser = FileChooser(start_path, title='选择已有的标注CSV文件'); self.existing_csv_chooser.filter_pattern = ['*.csv']; self.load_existing_button = widgets.Button(description='加载文件进行匹配', icon='folder-open', button_style='info'); self.mapping_box = widgets.VBox([], visible=False, layout=box_layout); self.start_editing_button = widgets.Button(description='开始编辑', icon='pencil', button_style='success', visible=False)
        tab2_content = widgets.VBox([self.existing_csv_chooser, self.load_existing_button, self.mapping_box, self.start_editing_button])
        self.blank_width_input = widgets.IntText(value=50, description='画布宽度 (spots):', style={'description_width': 'initial'}); self.blank_height_input = widgets.IntText(value=50, description='画布高度 (spots):', style={'description_width': 'initial'}); self.create_blank_button = widgets.Button(description='创建空白画布并编辑', button_style='info', icon='square-o')
        blank_box = widgets.VBox([self.blank_width_input, self.blank_height_input, self.create_blank_button], layout=box_layout); tab3_content = widgets.VBox([blank_box])
        self.tab_widget = widgets.Tab(children=[tab1_content, tab2_content, tab3_content]); self.tab_widget.set_title(0, '从图像生成'); self.tab_widget.set_title(1, '加载已有标注'); self.tab_widget.set_title(2, '创建空白画布')
        self.tool_container = widgets.Output(); self.app_layout = widgets.VBox([widgets.HTML("<h1>多功能空间注释平台</h1><hr>"), self.tab_widget, self.tool_container])
        self.barcode_chooser_img.register_callback(self._on_barcode_file_selected)
        self.generate_button.on_click(self._on_generate_click); self.load_existing_button.on_click(self._on_load_existing_click); self.start_editing_button.on_click(self._on_start_editing_click); self.create_blank_button.on_click(self._on_create_blank_click)
    def _on_barcode_file_selected(self, chooser):
        barcode_path = chooser.selected
        if barcode_path and os.path.exists(barcode_path):
            try: cols = pd.read_csv(barcode_path, nrows=0).columns.tolist(); self.img_x_map_dd.options = cols; self.img_y_map_dd.options = cols; self.img_mapping_box.visible = True
            except Exception: self.img_mapping_box.visible = False
        else: self.img_mapping_box.visible = False
    def _on_generate_click(self, b):
        self.tool_container.clear_output(wait=True)
        with self.tool_container:
            img_path = self.image_chooser.selected; barcode_path = self.barcode_chooser_img.selected
            if not img_path or not os.path.exists(img_path): print("错误：请选择一个有效的图像文件。"); return
            grid_w = self.grid_width_input.value; grid_h = self.grid_height_input.value
            if barcode_path and os.path.exists(barcode_path):
                spatial_df = pd.read_csv(barcode_path); x_col = self.img_x_map_dd.value; y_col = self.img_y_map_dd.value; spatial_df.rename(columns={x_col: 'x_coord', y_col: 'y_coord'}, inplace=True)
                if 'barcode' not in spatial_df.columns: print("警告：坐标文件中无 'barcode' 列，将自动生成。"); spatial_df['barcode'] = [f"spot_{r.y_coord}_{r.x_coord}" for r in spatial_df.itertuples()]
            else:
                print("提示：未提供坐标CSV，将自动生成占位符barcodes。")
                barcodes = [f"spot_{y}_{x}" for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)]; x_coords = [x for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)]; y_coords = [y for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)]
                spatial_df = pd.DataFrame({'barcode': barcodes, 'x_coord': x_coords, 'y_coord': y_coords})
            params = {'grid_width': grid_w, 'grid_height': grid_h, 'n_types': self.n_types_input.value, 'correct_near_black': self.correct_black_checkbox.value, 'near_black_threshold': self.black_threshold_input.value, 'remove_background': self.remove_background_checkbox.value, 'background_color_str': self.background_color_input.value}
            auto_annotations_df = process_cell_type_map(img_path, spatial_df, **params)
            if not auto_annotations_df.empty:
                print("\n--- 自动注释完成！正在启动交互式编辑器... ---")
                annotator = CellTypeAnnotator(annotation_df=auto_annotations_df); annotator.display_tool()
            else: print("\n错误：自动注释过程未能生成任何结果。")
    def _on_load_existing_click(self, b):
        csv_path = self.existing_csv_chooser.selected
        if not csv_path or not os.path.exists(csv_path):
            with self.tool_container: clear_output(); print("错误：请选择一个有效的CSV文件。")
            return
        self.loaded_df = pd.read_csv(csv_path); cols = self.loaded_df.columns.tolist()
        self.x_map_dd = widgets.Dropdown(options=cols, description="X坐标列:"); self.y_map_dd = widgets.Dropdown(options=cols, description="Y坐标列:"); self.type_map_dd = widgets.Dropdown(options=cols, description="类型列:")
        self.mapping_box.children = [widgets.HTML("<b>请匹配您的CSV列名:</b>"), self.x_map_dd, self.y_map_dd, self.type_map_dd]
        self.mapping_box.visible = True; self.start_editing_button.visible = True
    def _on_start_editing_click(self, b):
        self.tool_container.clear_output(wait=True)
        with self.tool_container:
            x_col = self.x_map_dd.value; y_col = self.y_map_dd.value; type_col = self.type_map_dd.value
            if len({x_col, y_col, type_col}) < 3: print("错误：请为X, Y, 类型选择不同的列。"); return
            df = self.loaded_df.rename(columns={x_col: 'grid_x', y_col: 'grid_y', type_col: 'cell_type'})
            if 'barcode' not in df.columns: df['barcode'] = [f"spot_{r.grid_y}_{r.grid_x}" for r in df.itertuples()]
            if 'color' not in df.columns: df['color'] = [(128, 128, 128)] * len(df)
            print("\n--- 文件加载成功！正在启动交互式编辑器... ---")
            annotator = CellTypeAnnotator(annotation_df=df); annotator.display_tool()
    def _on_create_blank_click(self, b):
        self.tool_container.clear_output(wait=True)
        with self.tool_container:
            grid_w = self.blank_width_input.value; grid_h = self.blank_height_input.value
            barcodes = [f"spot_{y}_{x}" for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)]; x_coords = [x for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)]; y_coords = [y for y in range(1, grid_h + 1) for x in range(1, grid_w + 1)]
            df = pd.DataFrame({'barcode': barcodes, 'grid_x': x_coords, 'grid_y': y_coords, 'cell_type': 'Unassigned', 'color': [(200, 200, 200)] * (grid_w * grid_h)})
            print("\n--- 空白画布创建成功！正在启动交互式编辑器... ---")
            annotator = CellTypeAnnotator(annotation_df=df); annotator.display_tool()
    def display_app(self):
        display(self.app_layout)