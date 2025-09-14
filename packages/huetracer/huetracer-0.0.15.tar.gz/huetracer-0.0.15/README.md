# HueTracer <img src="src/HueTracer.jpg" width=50>
## Cell-cell interaction prediction model for Visium HD spatial transcriptome platform
HueTracer is software for analyzing cell-cell interactions at single-cell resolution using Visium HD. It identifies cell positions using the Bin2Cell algorithm. It performs cell typing using label transfer from cell annotations in single-cell analysis or by combining Visium HD tissue images with gene expression profiles. It performs microenvironment clustering based on the expression patterns of cells surrounding each cell. It identifies cell-cell interactions using the NicheNet database.  
  
HueTracer is a software program created as a follow-up to [DeepCOLOR](https://github.com/kojikoji/deepcolor) software.  


## Instalation
You can install HueTracer using pip command from your shell.
```shell
pip install huetracer
```

## Usage
You need to prepare Visium HD spatial transcriptome data generated with SpaceRanger program by 10X. You can see the usage as follows.

#### Visium HD giant cell tumor sample (with version 0.0.15)
Our own tumor samples, 10X Chromium and Visium HD analyses  
- [Nucleus segmentation tutorial](tutorial/nucleus_segmentation_tutorial.ipynb)  
- [Cell type annotation for single cell transcriptome tutorial](tutorial/single_cell_annotation_tutorial.ipynb)  
- [Cell type label transfer tutorial](tutorial/label_transfer_tutorial.ipynb)  
- [Microenvironment prediction tutorial](tutorial/microenvironment_tutorial.ipynb)  
- [Cell-cell interaction tutorial](tutorial/cell_cell_interaction_tutorial.ipynb)  
nucleus_segmentation_tutorial_without_single_cell_data
  
#### Visium HD mouse sample without single-cell data (with version 0.0.15)
Our own tumor sample, Visium HD analyses  
- [Nucleus segmentation tutorial](tutorial/nucleus_segmentation_tutorial_without_single_cell_data.ipynb)  
- [Cell type annotation tutorial](tutorial/label_transfer_tutorial_without_single_cell_data.ipynb)  
- [Microenvironment prediction tutorial](tutorial/microenvironment_tutorial_without_single_cell_data.ipynb)  
- [Cell-cell interaction tutorial](tutorial/cell_cell_interaction_tutorial_without_single_cell_data.ipynb)  
  
#### Visium HD colon adenocarcinoma sample obtained from 10X website (with version 0.0.15)
Download Chromium/Visium HD files.  
[Chromium single cell transctiptome aggregated files](https://www.10xgenomics.com/platforms/visium/product-family/dataset-human-crc), Feature barcode matrix (filtered)  
[Visium HD spatial transcriptome P2 CRC files](https://www.10xgenomics.com/jp/datasets/visium-hd-cytassist-gene-expression-libraries-of-human-crc), Binned outputs (all bin levels), Microscope image (BTF)  
  
- [Nucleus segmentation tutorial](tutorial/nucleus_segmentation_tutorial_10x.ipynb)  
  As BTF file is too large to handle with Bin2Cell, a cropped image will be used in this tutorial. That is not always necessary for other samples.  
- [Cell type annotation for single cell transcriptome tutorial](tutorial/single_cell_annotation_tutorial_10x.ipynb)  
- [Cell type label transfer tutorial](tutorial/label_transfer_tutorial_10x.ipynb)  
- [Microenvironment prediction tutorial](tutorial/microenvironment_tutorial_10x.ipynb)  
- [Cell-cell interaction tutorial](tutorial/cell_cell_interaction_tutorial_10x.ipynb)  
