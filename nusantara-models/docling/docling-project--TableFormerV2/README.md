---
license: apache-2.0
library_name: docling
pipeline_tag: image-to-text
tags:
  - docling
  - table-structure-recognition
  - document-conversion
  - tables
  - pdf
  - preview
---

# TableFormerV2

> [!WARNING]
> **Preview model.** TableFormerV2 is a preview release. Its weights, outputs, and
> integration options can change in future releases without notice. The default
> table structure model in Docling is still
> [TableFormer V1](https://huggingface.co/docling-project/docling-models).

TableFormerV2 is a table structure recognition model for
[Docling](https://github.com/docling-project/docling). It takes an image of a
table and predicts its structure as an
[OTSL](https://arxiv.org/abs/2305.03393) token sequence, together with a
bounding box for each cell. Docling then maps the cells back to the text of the
document to build a `TableItem` in the `DoclingDocument`.

## Model details

| | |
|---|---|
| **Developed by** | IBM Research, for the Docling project |
| **Model type** | Image-to-sequence (table structure + cell boxes) |
| **Parameters** | ~52M (FP32) |
| **Input** | Table crop, resized to 448×448 |
| **Output** | OTSL structure tokens and one bounding box per cell |
| **License** | Apache-2.0 |
| **Status** | Preview |

### Architecture

- **Image encoder:** EfficientNetV2-S backbone with Squeeze-and-Excitation.
- **Spatial mixer:** depthwise separable convolutions (no self-attention in the
  encoder).
- **Structure decoder:** cache-aware Transformer decoder with cross-attention to
  the image features.
- **Bounding-box head:** multi-layer attention decoder that predicts one box per
  cell.

The design is lightweight. It targets fast CPU inference and GPU batch
inference.

The model implementation is in
[`docling-ibm-models`](https://github.com/docling-project/docling-ibm-models)
(`docling_ibm_models.tableformer_v2`).

## Usage with Docling

Install Docling:

```bash
pip install docling
```

Docling downloads the weights from this repository automatically the first time
you use the model. To download them before you run a conversion (for example,
for offline use), run:

```bash
docling-tools models download tableformerv2
```

### Option 1: Use the preset

The fastest way to enable TableFormerV2 is to select it by name.

**CLI:**

```bash
docling report.pdf --table-structure-engine docling_tableformer_v2
```

**Docling Serve / Service Client:** set the `tableformer_v2` preset.

```python
from docling.datamodel.service.options import ConvertDocumentsOptions
from docling.service_client import DoclingServiceClient

options = ConvertDocumentsOptions(table_structure_preset="tableformer_v2")

with DoclingServiceClient(url="http://localhost:5001") as client:
    result = client.convert(source="report.pdf", options=options)
    print(result.document.export_to_markdown())
```

### Option 2: Set the full pipeline options

Use the Python SDK when you need full control over the pipeline. Set
`table_structure_options` to `TableStructureV2Options`:

```python
from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureV2Options,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions(
    do_table_structure=True,
    table_structure_options=TableStructureV2Options(
        # True:  match the predicted cells to the text cells of the PDF.
        # False: use the cells predicted by the model and ignore the PDF cells.
        do_cell_matching=True,
    ),
    accelerator_options=AcceleratorOptions(device="auto", num_threads=8),
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
    }
)

result = converter.convert("report.pdf")

for table in result.document.tables:
    print(table.export_to_dataframe())
```

To load pre-downloaded weights, set `artifacts_path` on the pipeline options:

```python
pipeline_options = PdfPipelineOptions(
    artifacts_path="/path/to/models",  # contains docling-project--TableFormerV2/
    table_structure_options=TableStructureV2Options(),
)
```

### Options

| Option | Default | Description |
|---|---|---|
| `do_cell_matching` | `True` | Match the predicted cells to the PDF text cells. Set to `False` if PDF cells span more than one column, because this can break the table output. |

## Limitations

- This is a **preview** model. Quality and behavior can change between
  releases.
- On Apple Silicon, the model runs on CPU. Docling does not use MPS for this
  model.
- The model sees only the table crop. Errors in the layout model (missed or
  wrongly cropped tables) propagate to the table structure.

## License

This model is released under the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Citation

If you use TableFormerV2, please cite Docling:

```bibtex
@misc{Docling,
  author = {Docling Team},
  title = {Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion},
  url = {https://arxiv.org/abs/2501.17887},
  eprint = {2501.17887},
  archivePrefix = {arXiv},
  doi = {10.48550/arXiv.2501.17887},
  year = {2025}
}
```
