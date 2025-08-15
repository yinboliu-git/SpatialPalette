# SpatialPalette (空间注释调色板)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**一个在 Jupyter 环境中运行的、用于半自动空间组织图谱注释与交互式校正的多功能平台。**

**An all-in-one Jupyter-based platform for semi-automatic annotation and interactive correction of spatial tissue maps.**

---
![SpatialPalette Demo](docs/app.gif)

## 📖 简介 (Introduction)

在空间组学分析中，准确地为组织切片上的不同区域进行注释是至关重要的一步。手动标注不仅耗时耗力，而且难以保证可重复性。SpatialPalette 旨在解决这一痛点，它提供了一个从组织学标注图像到最终校正后、机器可读的标注文件的完整工作流。

本平台巧妙地结合了基于颜色聚类的**自动注释**能力和一个功能强大的**交互式图形编辑器**，让研究人员可以快速生成初始注释，并对其进行精细的手动校正和管理，所有操作都在熟悉的 Jupyter Notebook 环境中完成。

## ✨ 主要功能 (Features)

#### 1. 三种灵活的工作模式
- **🎨 从图像生成 (Generate from Image)**: 上传组织图像 (如 TIFF, JPG, PNG) 和可选的空间坐标文件，通过一系列可调参数（网格大小、目标类别数、背景移除等），自动生成初始的区域注释。
- **📂 加载已有标注 (Load Existing Annotation)**: 直接加载一个外部的 CSV 标注文件（支持自定义列名匹配），立即进入交互式编辑模式。
- **⬜ 创建空白画布 (Create Blank Canvas)**: 无需任何输入文件，快速创建一个指定大小的空白网格画布，用于从零开始的纯手动标注。

#### 2. 强大的交互式编辑器
- **🎯 高级套索选择 (Advanced Lasso Selection)**:
  - **实时高亮**: 选中的点会立刻出现黑色边框，方便确认。
  - **增选**: 按住 `Shift` 键进行选择，可将新选中的点**添加**到现有选区。
  - **减选**: 按住 `Ctrl` (Windows) 或 `Cmd` (Mac) 键，可从当前选区中**移除**点。
- **✍️ 点编辑 (Point Editing)**:
  - **更新类型**: 将任意选中点快速更改为目标细胞类型。
  - **删除点**: 从画布中彻底移除选中的一个或多个点。
- **🗂️ 类别管理 (Category Management)**:
  - **创建**: 随时添加新的细胞类型名称。
  - **重命名**: 为已有的类别更换名称。
  - **删除**: 删除整个类别，并可选择是**一并移除**该类的所有点，还是将它们归为**“未分配 (Unassigned)”**。
- **↩️ 多步撤销 (Multi-Level Undo)**: 支持对所有编辑操作（更新、删除、重命名、创建类别）进行多达20步的撤销，确保操作安全。

#### 3. 智能的自动化引擎
- **🤖 K-Means 颜色聚类**: 自动分析图像中的颜色分布，将视觉上相近的颜色智能地合并为您指定的 N 个类别。
- **🧹 智能后处理**:
    - **精确采样**: 采用“区域投票”机制，取每个网格中出现次数最多的颜色作为代表色，结果更准确。
    - **近黑修正**: 通过迭代式邻里校正算法，自动清除无意义的黑色/近黑色区域，并用周围最合理的主流类型进行填充。

#### 4. 便捷的导出功能
- **💾 保存数据**: 将您手动校正后的最终注释结果保存为一个包含 `barcode`, `grid_x`, `grid_y`, `cell_type` 等信息的干净CSV文件。
- **🖼️ 导出图片**: 一键将当前画布的视图导出为**PNG**, **SVG**, 或 **PDF** 格式的高质量图片，可直接用于报告或论文。

## 🚀 安装指南 (Installation)

1.  **克隆或下载本项目**
    ```bash
    git clone https://github.com/yinboliu-git/SpatialPalette.git
    cd SpatialPalette
    ```

2.  **创建并激活 Conda 环境 (推荐)**
    ```bash
    conda create -n spatialpalette_env python=3.9
    conda activate spatialpalette_env
    ```

3.  **安装依赖**
    进入项目根目录，通过 `requirements.txt` 文件一键安装所有必需的Python库。
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置 JupyterLab (首次使用需要)**
    如果您使用的是 JupyterLab，`ipywidgets` 和 `ipympl` 的前端扩展通常会通过 `conda` 或 `pip` 自动安装和启用。如果遇到问题，请确保 `jupyterlab` 和 `ipywidgets` 是最新的。
    ```bash
    conda install -c conda-forge jupyterlab ipywidgets
    ```
    *注意: 安装或更新后，强烈建议重启JupyterLab。*

## 💡 如何使用 (Usage)

1.  **启动 Jupyter**: 在项目根目录下，运行 `jupyter lab` 或 `jupyter notebook`。
2.  **打开 `example.ipynb`**: 在 Jupyter 中打开 `example.ipynb` 文件。
3.  **运行代码**: 按顺序运行 Notebook 中的代码单元格。
4.  **开始使用**: 功能全面的注释平台界面就会出现。
    - 在**选项卡 (Tabs)** 中选择您的工作模式（从图像生成 / 加载已有 / 创建空白）。
    - 根据界面提示，选择文件、设置参数，然后点击相应按钮启动交互式编辑器。
    - 在编辑器中进行您的所有手动校正。
    - 完成后，在编辑器下方的“保存与导出”区域保存您的工作成果。
