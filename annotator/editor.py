# annotator/editor.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path
import ipywidgets as widgets
from IPython.display import display
import ast, os

class CellTypeAnnotator:
    """
    一个功能全面的、在 Jupyter 中交互式注释细胞类型的工具 (最终版)
    """
    def __init__(self, annotation_df: pd.DataFrame):
        plt.ioff(); self.fig, self.ax = plt.subplots(figsize=(7, 7)); plt.ion()
        
        self.df = annotation_df.copy()
        if 'color' in self.df.columns and not self.df.empty and isinstance(self.df['color'].iloc[0], str):
            try: self.df['color'] = self.df['color'].apply(ast.literal_eval)
            except (ValueError, SyntaxError): print("警告: 'color' 列包含无效格式。")
        
        self.df_history = [self.df.copy()]
        if 'cell_type' not in self.df.columns: self.df['cell_type'] = 'Unassigned'
        self.df['cell_type'] = self.df['cell_type'].astype(str)
        self.unique_types_initial = sorted(list(self.df['cell_type'].unique()))
        self.types_history = [self.unique_types_initial.copy()]
        
        self.selected_indices = np.array([], dtype=int)
        self.highlight_plot = None
        self.shift_pressed = False
        self.ctrl_pressed = False
        
        self._create_widgets()
        self._update_plot()
        
        # 连接鼠标和键盘事件
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self._on_key_release)
        self.fig.canvas.mpl_connect('button_press_event', self._on_canvas_click)

    def _create_widgets(self):
        """(已更新) 创建所有UI控件，增加新增点和即时创建新类型功能"""
        self.unique_types_initial = sorted(self.df['cell_type'].unique())
        
        # --- 编辑点控件 ---
        self.add_point_toggle = widgets.ToggleButton(value=False, description='新增点模式', tooltip='激活后，单击画布可新增点', icon='plus-circle')
        self.type_dropdown = widgets.Dropdown(options=self.unique_types_initial, description='目标类型:')
        self.update_as_new_input = widgets.Text(value='', placeholder='...或设为新类型', description='', layout=widgets.Layout(width='150px'))
        self.update_button = widgets.Button(description="更新选中点", icon='pencil', button_style='primary')
        self.delete_points_button = widgets.Button(description="删除选中点", icon='trash', button_style='danger')
        
        edit_points_box = widgets.VBox([
            widgets.HTML("<b>1. 用套索选择 (按住Shift增选, Ctrl/Cmd减选) 或激活新增点模式</b>"),
            widgets.HBox([self.type_dropdown, self.update_as_new_input, self.update_button]),
            widgets.HBox([self.add_point_toggle, self.delete_points_button])
        ])
        
        # --- 类别管理控件 (不变) ---
        self.new_type_input = widgets.Text(value='', placeholder='输入新类别名', description='新类别名:')
        self.create_type_button = widgets.Button(description="创建", icon='plus', button_style='success')
        self.rename_from_dropdown = widgets.Dropdown(options=self.unique_types_initial, description='旧名称:')
        self.rename_to_input = widgets.Text(value='', placeholder='输入新名称', description='新名称:')
        self.rename_button = widgets.Button(description="重命名", icon='edit')
        self.delete_type_dropdown = widgets.Dropdown(options=self.unique_types_initial, description='要删除的类别:')
        self.delete_points_checkbox = widgets.Checkbox(value=True, description='同时删除属于该类型的点')
        self.delete_type_button = widgets.Button(description="删除类别", icon='trash-o', button_style='danger')
        manage_categories_box = widgets.VBox([widgets.HTML("<b>创建新类别:</b>"), widgets.HBox([self.new_type_input, self.create_type_button]), widgets.HTML("<hr style='margin: 10px 0;'>"), widgets.HTML("<b>重命名类别:</b>"), widgets.HBox([self.rename_from_dropdown, self.rename_to_input, self.rename_button]), widgets.HTML("<hr style='margin: 10px 0;'>"), widgets.HTML("<b>删除类别:</b>"), widgets.HBox([self.delete_type_dropdown, self.delete_points_checkbox, self.delete_type_button])])
        
        self.accordion = widgets.Accordion(children=[edit_points_box, manage_categories_box])
        self.accordion.set_title(0, '编辑点 (Edit Points)'); self.accordion.set_title(1, '管理类别 (Manage Categories)')
        
        self.undo_button = widgets.Button(description="撤销上一步 (Undo)", icon='undo', button_style='warning', disabled=True)
        self.info_label = widgets.HTML(value="<b>状态:</b> 欢迎！请用鼠标在图上框选点。")

        self.filename_input = widgets.Text(value='corrected_annotations.csv', description='输出文件名:', style={'description_width': 'initial'})
        self.save_button = widgets.Button(description="保存到 CSV", icon='save', button_style='success')
        self.export_png_button = widgets.Button(description="导出 PNG", icon='file-image-o'); self.export_svg_button = widgets.Button(description="导出 SVG", icon='file-image-o'); self.export_pdf_button = widgets.Button(description="导出 PDF", icon='file-pdf-o')
        save_box = widgets.VBox([widgets.HTML("<hr><b>保存与导出:</b>"), widgets.HBox([self.filename_input, self.save_button]), widgets.HBox([self.export_png_button, self.export_svg_button, self.export_pdf_button])])

        self.controls_layout = widgets.VBox([self.info_label, self.accordion, self.undo_button, save_box])

        # --- 绑定所有事件 ---
        self.add_point_toggle.observe(self._on_add_mode_toggle, names='value')
        self.update_button.on_click(self._on_update_click); self.delete_points_button.on_click(self._on_delete_points_click); self.create_type_button.on_click(self._on_create_type_click); self.rename_button.on_click(self._on_rename_click); self.delete_type_button.on_click(self._on_delete_type_click); 
        self.save_button.on_click(self._on_save_click); self.undo_button.on_click(self._on_undo_click);
        self.export_png_button.on_click(lambda b: self._export_image('png')); self.export_svg_button.on_click(lambda b: self._export_image('svg')); self.export_pdf_button.on_click(lambda b: self._export_image('pdf'))

    def _on_add_mode_toggle(self, change):
        """当新增点模式开关状态改变时"""
        if change['new']:
            self.info_label.value = "<b>状态:</b> <font color='blue'>新增点模式已激活</font>。单击画布添加点。"
            if self.lasso: self.lasso.active = False
            self.fig.canvas.set_cursor(2)
        else:
            self.info_label.value = "<b>状态:</b> 新增点模式已关闭。"
            if self.lasso: self.lasso.active = True
            self.fig.canvas.set_cursor(1)

    def _on_canvas_click(self, event):
        """当画布被点击时 (仅在新增点模式下生效)"""
        if not self.add_point_toggle.value or event.button != 1 or event.inaxes != self.ax: return
        
        x, y = int(round(event.xdata)), int(round(event.ydata))
        
        if not self.df[(self.df['grid_x'] == x) & (self.df['grid_y'] == y)].empty:
            self.info_label.value = f"<b>状态:</b> <font color='orange'>点 ({x}, {y}) 已存在，无法添加。</font>"
            return
            
        self._save_state_for_undo()
        
        target_type = self.type_dropdown.value
        new_barcode = f"manual_spot_{y}_{x}"
        # 获取目标类型的颜色，如果没有则用灰色
        color_tuple = tuple(int(c*255) for c in self.color_map.get(target_type, (0.5,0.5,0.5))[:3])

        new_point = pd.DataFrame([{'barcode': new_barcode, 'grid_x': x, 'grid_y': y, 'cell_type': target_type, 'color': color_tuple}])
        self.df = pd.concat([self.df, new_point], ignore_index=True)
        self._update_plot_after_action(f"在 ({x}, {y}) 新增 1 个点。")

    def _on_update_click(self, b):
        """(已更新) 当'更新'按钮被点击时，支持即时创建新类型"""
        if len(self.selected_indices) == 0:
            self.info_label.value = "<b>状态:</b> <font color='red'>未选中任何点。</font>"; return
        
        self._save_state_for_undo()
        
        new_type_name = self.update_as_new_input.value.strip()
        if new_type_name:
            target_type = new_type_name
            if target_type not in self.unique_types_initial:
                self.unique_types_initial.append(target_type)
                self._update_dropdowns()
        else:
            target_type = self.type_dropdown.value
            
        self.df.iloc[self.selected_indices, self.df.columns.get_loc('cell_type')] = target_type
        self.update_as_new_input.value = ''
        self._update_plot_after_action("更新成功！")
        
    # (其余所有函数，如 _update_plot, _on_delete_points_click 等都与上一版相同)
    def _export_image(self, file_format: str): base_filename, _ = os.path.splitext(self.filename_input.value); output_filename = f"{base_filename}.{file_format}"; self.fig.savefig(output_filename, dpi=300, bbox_inches='tight'); self.info_label.value = f"<b>状态:</b> <font color='blue'>图片已成功保存到 {output_filename}</font>"
    def _on_save_click(self, b):
        output_filename = self.filename_input.value
        try:
            final_df = self.df.copy(); current_types = sorted(list(final_df['cell_type'].unique())); palette = plt.get_cmap('tab10'); self.color_map = {ctype: palette(i % 10) for i, ctype in enumerate(current_types)}; self.color_map['Unassigned'] = (0.8, 0.8, 0.8, 1.0)
            type_to_rgb_map = {ctype: tuple(int(c*255) for c in color[:3]) for ctype, color in self.color_map.items()}; final_df['color'] = final_df['cell_type'].map(type_to_rgb_map).fillna(str((0,0,0)))
            if not output_filename.endswith('.csv'): base, _ = os.path.splitext(output_filename); output_filename = base + '.csv'
            final_df.to_csv(output_filename, index=False, columns=['barcode', 'grid_x', 'grid_y', 'cell_type', 'color']); self.info_label.value = f"<b>状态:</b> <font color='green'>成功保存到 {output_filename}</font>"
        except Exception as e: self.info_label.value = f"<b>状态:</b> <font color='red'>保存失败: {e}</font>"
    def display_tool(self): main_container = widgets.VBox([self.fig.canvas, self.controls_layout]); main_container.layout.margin = '0 0 0 50px'; display(main_container)
    def _save_state_for_undo(self): self.df_history.append(self.df.copy()); self.types_history.append(self.unique_types_initial.copy()); self.undo_button.disabled = False
    def _update_plot(self):
        self.ax.clear(); unique_types_filtered = sorted([t for t in self.unique_types_initial if t != 'Unassigned']); palette = plt.get_cmap('tab10'); self.color_map = {ctype: palette(i % 10) for i, ctype in enumerate(unique_types_filtered)}; self.color_map['Unassigned'] = (0.8, 0.8, 0.8, 1.0)
        for cell_type, color in self.color_map.items():
            subset = self.df[self.df['cell_type'] == cell_type]
            if not subset.empty: self.ax.scatter(subset['grid_x'], subset['grid_y'], c=[color], label=cell_type, s=50)
        self.ax.set_title('Interactive Cell Type Annotation'); self.ax.set_aspect('equal', adjustable='box'); self.ax.invert_yaxis(); self.ax.legend(title='Cell Types', bbox_to_anchor=(1.05, 1), loc='upper left'); self.ax.grid(True, linestyle='--', alpha=0.5); self.fig.tight_layout(rect=[0, 0, 0.85, 1]); self.lasso = LassoSelector(self.ax, self._on_select); self.fig.canvas.draw_idle()
    def _update_dropdowns(self): sorted_types = sorted(self.unique_types_initial); self.type_dropdown.options = sorted_types; self.rename_from_dropdown.options = sorted_types; self.delete_type_dropdown.options = sorted_types
    def _on_key_press(self, event):
        if event.key == 'shift': self.shift_pressed = True
        if event.key in ['control', 'super', 'cmd']: self.ctrl_pressed = True
    def _on_key_release(self, event):
        if event.key == 'shift': self.shift_pressed = False
        if event.key in ['control', 'super', 'cmd']: self.ctrl_pressed = False
    def _on_select(self, vertices):
        path = Path(vertices); points = self.df[['grid_x', 'grid_y']].values; newly_selected_indices = np.nonzero(path.contains_points(points))[0]
        current_selection_set = set(self.selected_indices); new_selection_set = set(newly_selected_indices)
        if self.shift_pressed: updated_selection_set = current_selection_set.union(new_selection_set)
        elif self.ctrl_pressed: updated_selection_set = current_selection_set.difference(new_selection_set)
        else: updated_selection_set = new_selection_set
        self.selected_indices = np.array(list(updated_selection_set), dtype=int)
        self._highlight_selection(); self.info_label.value = f"<b>状态:</b> 已选中 {len(self.selected_indices)} 个点。"
    def _highlight_selection(self):
        if self.highlight_plot: self.highlight_plot.remove()
        if self.selected_indices.size > 0:
            selected_data = self.df.iloc[self.selected_indices]
            self.highlight_plot = self.ax.scatter(selected_data['grid_x'], selected_data['grid_y'], facecolors='none', edgecolors='black', s=80, linewidth=1.5, label='_nolegend_')
        else: self.highlight_plot = None
        self.fig.canvas.draw_idle()
    def _update_plot_after_action(self, msg): self.selected_indices = np.array([], dtype=int); self._update_plot(); self.info_label.value = f"<b>状态:</b> <font color='green'>{msg}</font> {len(self.df)} 个点剩余。"
    def _on_delete_points_click(self, b): self._save_state_for_undo(); num_deleted = len(self.selected_indices); self.df.drop(self.df.index[self.selected_indices], inplace=True); self.df.reset_index(drop=True, inplace=True); self._update_plot_after_action(f"删除了 {num_deleted} 个点！")
    def _on_create_type_click(self, b): new_name = self.new_type_input.value.strip(); self._save_state_for_undo(); self.unique_types_initial.append(new_name); self._update_dropdowns(); self._update_plot(); self.info_label.value = f"<b>状态:</b> <font color='green'>成功创建新类别: '{new_name}'</font>"; self.new_type_input.value = ''
    def _on_rename_click(self, b): old_name = self.rename_from_dropdown.value; new_name = self.rename_to_input.value.strip(); self._save_state_for_undo(); self.df.loc[self.df['cell_type'] == old_name, 'cell_type'] = new_name; self.unique_types_initial = [new_name if t == old_name else t for t in self.unique_types_initial]; self._update_dropdowns(); self._update_plot(); self.info_label.value = f"<b>状态:</b> <font color='green'>成功将 '{old_name}' 重命名为 '{new_name}'。</font>"; self.rename_to_input.value = ''
    def _on_delete_type_click(self, b):
        type_to_delete = self.delete_type_dropdown.value
        if type_to_delete is None: self.info_label.value = "<b>状态:</b> <font color='red'>没有可删除的类别。</font>"; return
        self._save_state_for_undo()
        if self.delete_points_checkbox.value:
            num_deleted = len(self.df[self.df['cell_type'] == type_to_delete]); self.df = self.df[self.df['cell_type'] != type_to_delete].reset_index(drop=True); self.info_label.value = f"<b>状态:</b> <font color='green'>已删除类别 '{type_to_delete}' 及其包含的 {num_deleted} 个点。</font>"
        else:
            self.df.loc[self.df['cell_type'] == type_to_delete, 'cell_type'] = 'Unassigned'
            if 'Unassigned' not in self.unique_types_initial: self.unique_types_initial.append('Unassigned')
            self.info_label.value = f"<b>状态:</b> <font color='green'>已将类别 '{type_to_delete}' 的所有点重置为 'Unassigned'。</font>"
        if type_to_delete in self.unique_types_initial: self.unique_types_initial.remove(type_to_delete)
        self._update_dropdowns(); self._update_plot()
    def _on_undo_click(self, b):
        if len(self.df_history) > 1:
            self.df_history.pop(); self.types_history.pop(); self.df = self.df_history[-1].copy(); self.unique_types_initial = self.types_history[-1].copy(); self._update_dropdowns(); self._update_plot(); self.info_label.value = "<b>状态:</b> 操作已撤销。"; self.undo_button.disabled = len(self.df_history) <= 1
