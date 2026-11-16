"""OCR Ground Truth Evaluation Framework.

Measures CER (Character Error Rate) and WER (Word Error Rate)
between OCR-extracted text and manually transcribed ground truth.
"""
import sys, os, json, re
sys.path.insert(0, 'C:/Users/dmaza/mcp-starter')

def levenshtein_distance(s1, s2):
    """Compute Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev[j + 1] + 1
            deletions = curr[j] + 1
            substitutions = prev[j] + (c1 != c2)
            curr.append(min(insertions, deletions, substitutions))
        prev = curr
    return prev[-1]

def compute_cer(ocr_text, ground_truth):
    """Compute Character Error Rate."""
    ocr = ocr_text.strip().lower()
    gt = ground_truth.strip().lower()
    if len(gt) == 0:
        return 1.0 if len(ocr) > 0 else 0.0
    dist = levenshtein_distance(ocr, gt)
    return dist / len(gt)

def compute_wer(ocr_text, ground_truth):
    """Compute Word Error Rate."""
    ocr_words = ocr_text.strip().lower().split()
    gt_words = ground_truth.strip().lower().split()
    if len(gt_words) == 0:
        return 1.0 if len(ocr_words) > 0 else 0.0
    # Word-level Levenshtein
    dist = levenshtein_distance(' '.join(ocr_words), ' '.join(gt_words))
    # Approximate WER using word-level
    # Better: use sequence matching
    import difflib
    sm = difflib.SequenceMatcher(None, ocr_words, gt_words)
    matches = sm.find_longest_match(0, len(ocr_words), 0, len(gt_words))
    # Simple WER approximation
    errors = abs(len(ocr_words) - len(gt_words))
    # Count substitutions
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('replace', 'delete', 'insert'):
            errors += max(i2-i1, j2-j1)
    return min(1.0, errors / max(len(gt_words), 1))

def evaluate_ocr(pdf_path, ground_truth_text):
    """Evaluate OCR quality for a PDF."""
    from app.knowledge.engine import KnowledgeEngine
    ke = KnowledgeEngine()
    raw = open(pdf_path, 'rb').read()
    pages = ke._extract_pdf_pages(raw)
    ocr_text = '\n'.join(pages)
    cer = compute_cer(ocr_text, ground_truth_text)
    wer = compute_wer(ocr_text, ground_truth_text)
    return {
        'cer': round(cer, 4),
        'wer': round(wer, 4),
        'ocr_chars': len(ocr_text),
        'gt_chars': len(ground_truth_text),
        'ocr_pages': len(pages),
    }

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: ocr_ground_truth_eval.py <pdf_path> <ground_truth_txt>')
        sys.exit(1)
    gt = open(sys.argv[2], encoding='utf-8').read()
    result = evaluate_ocr(sys.argv[1], gt)
    print(json.dumps(result, indent=2))
