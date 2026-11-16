# OCR Ground Truth Framework

## Purpose
Measure OCR quality (CER/WER) for scanned SOP PDFs.

## Usage
python scripts/ocr_ground_truth_eval.py <pdf_path> <ground_truth_txt>

## Ground Truth Files
- capil04_gt.txt: CAPIL_04.pdf (page 1 header)
- capil02_gt.txt: CAPIL_02.pdf (page 1 header)
- dafduk01_gt.txt: DAFDUK_01.pdf (page 1 header)
- capil01_gt.txt: CAPIL_01.pdf (page 1 header)
- dafduk22_gt.txt: DAFDUK_22.pdf (page 1 header)

## Note
Ground truth is manually transcribed from the scanned PDF.
CER = Character Error Rate (Levenshtein distance / ground truth length)
WER = Word Error Rate (word-level Levenshtein / ground truth word count)
