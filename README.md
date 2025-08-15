# SpatialPalette (空间注释调色板)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**一个用于空间组织图谱的半自动、交互式注释平台 (A semi-automatic, interactive annotation platform for spatial tissue maps)。**

---

### 效果演示 (Demo)

**(推荐)**: 强烈建议您在此处放置一张 GIF 动图，展示从选择文件、自动生成注释到手动框选校正的全过程。一张清晰的动图能让项目价值一目了然。

*您可以使用 [ScreenToGif](https://www.screentogif.com/) (Windows), [Kap](https://getkap.co/) (Mac), 或 [Peek](https://github.com/phw/peek) (Linux) 等免费工具轻松录制。*

![GIF Demo Placeholder](https://user-images.githubusercontent.com/10940172/204278809-9d7a2769-6d8c-4f46-95b6-897d1421c1f7.gif)

### 项目简介 (Introduction)

在空间组学分析中，准确地为组织切片上的不同区域赋予细胞类型或结构注释至关重要。传统方法通常依赖于在图像编辑软件（如 Photoshop）中手动描边，再通过复杂的脚本将其与空间坐标对齐，这一过程既繁琐又容易出错。

**SpatialPalette** 旨在解决这一痛点。它是一个在 Jupyter Notebook 环境中运行的一站式解决方案，通过一个强大的图形用户界面 (GUI)，将从组织图像到可用于下游分析的、精确的注释文件的全过程无缝衔接起来。它结合了机器学习的自动化效率和人类专家的精细校正能力。

### 核心功能 (Key Features)

- **🎨 多模式工作流**:
  - **从图像生成**: 上传组织学标注图 (如 `TIFF`, `JPG`, `PNG`)，通过颜色聚类自动生成初始注释。
  - **加载已有标注**: 加载一个外部的 CSV 标注文件，直接进入交互式编辑模式。
  - **创建空白画布**: 无需任何输入，创建一个指定大小的空白网格画布，用于从零开始手动标注。

- **⚙️ 强大的自动注释引擎**:
  - **颜色聚类**: 采用 K-Means 算法，能将视觉上相近的颜色区域智能合并为您指定的类别数量。
  - **精确采样**: 通过计算每个网格区域内的“颜色众数”来确定其代表色，而非简单的中心点采样，结果更准确。
  - **灵活的预处理**: 支持自定义网格宽度/高度、背景色移除、近黑区域修正等高级参数。

- **🖌️ 功能全面的交互式编辑器**:
  - **实时高亮与高级选择**:
    - **套索选择 (Lasso)**: 用鼠标自由框选任意形状的区域。
    - **高亮显示**: 选中的点会立刻出现黑色边框，方便确认。
    - **增选/减选**: 支持按住 `Shift` 键增选、按住 `Ctrl/Cmd` 键减选。
  - **丰富的编辑功能**:
    - **更新类型**: 将选中点批量更新为任一目标类型。
    - **删除点**: 从画布中彻底移除选中的点。
  - **完善的类别管理**:
    - **创建/重命名**: 自由添加新类别或为现有类别重命名。
    - **删除类别**: 可一键删除某个类别，并选择是将这些点彻底移除，还是将其归为“未分配 (Unassigned)”。
  - **多步撤销 (Undo)**: 支持最多20步的撤销操作，让您的所有修改都有“后悔药”。

- **💾 灵活的输入/输出**:
  - **文件浏览器**: 内置文件浏览器，让您可以自由选择系统内任意位置的文件。
  - **列名匹配**: 加载自定义 CSV 文件时，可通过下拉菜单轻松匹配坐标和类型所在的列。
  - **导出成果**: 将最终校正好的注释结果（包含 barcode, 网格坐标, 细胞类型, 代表色）保存为整洁的 `.csv` 文件。

### 安装指南 (Installation)

1.  **克隆或下载本项目**
    ```bash
    git clone [https://github.com/your-username/SpatialPalette.git](https://github.com/your-username/SpatialPalette.git)
    cd SpatialPalette
    ```

2.  **创建并激活 Conda 环境 (推荐)**
    ```bash
    conda create -n spatial-annotator python=3.9 -y
    conda activate spatial-annotator
    ```

3.  **安装依赖库**
    项目所需的所有依赖库都已在 `requirements.txt` 中列出。
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置 JupyterLab (首次使用)**
    如果您使用的是 JupyterLab，还需要确保 `ipywidgets` 扩展已正确安装。
    ```bash
    conda install -c conda-forge jupyterlab ipywidgets
    ```
    *注意: 安装后需要重启 JupyterLab 服务器。*

### 快速开始 (Quick Start)

1.  **启动 JupyterLab**
    在项目根目录下，运行:
    ```bash
    jupyter lab
