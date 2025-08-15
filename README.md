# 多功能空间注释平台 (Multifunctional Spatial Annotation Platform)

这是一个在 Jupyter Notebook 环境中运行的交互式工具，用于从组织图像创建、编辑和校正空间细胞类型注释。

## 主要功能

- **三种工作模式**:
  1.  **从图像生成**: 上传组织图像和可选的坐标文件，通过颜色聚类自动生成初始注释。
  2.  **加载已有标注**: 加载一个外部的CSV标注文件，直接进入编辑模式。
  3.  **创建空白画布**: 无需任何输入，创建一个空白的网格画布，用于从零开始手动标注。
- **高级自动标注参数**:
  - 自定义网格宽度和高度。
  - 自定义需要聚类成的细胞类型数量。
  - 自动移除背景、修正近黑区域，并可对相关参数进行微调。
- **强大的交互式编辑器**:
  - **套索选择工具**: 支持替换、增选 (Shift) 和减选 (Ctrl/Cmd)。
  - **实时高亮**: 选中的点会实时高亮，方便确认。
  - **编辑功能**: 可更新点类型、删除点。
  - **类别管理**: 可创建新类别、重命名类别、删除整个类别（可选择是否保留点）。
  - **多步撤销**: 支持最多20步的撤销操作，防止误操作。
  - **保存**: 将修改后的结果保存为新的CSV文件。

## 安装

1.  **克隆或下载本项目**
2.  **创建并激活 Conda 环境 (推荐)**
    ```bash
    conda create -n annotator_env python=3.9
    conda activate annotator_env
    ```
3.  **安装依赖**
    进入项目根目录，通过 `requirements.txt` 文件一键安装所有必需的Python库。
    ```bash
    pip install -r requirements.txt
    ```
4.  **配置 JupyterLab (首次使用需要)**
    如果您使用的是 JupyterLab，需要安装Jupyter widgets扩展以支持交互。
    ```bash
    conda install -c conda-forge jupyterlab ipywidgets
    ```
    *注意: 安装后可能需要重启JupyterLab。*

## 如何使用

1.  启动 JupyterLab: `jupyter lab`
2.  打开 `example.ipynb` 文件。
3.  按顺序运行其中的两个代码单元格。
4.  多功能注释平台的界面就会出现，您可以开始您的工作了！