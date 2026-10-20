"""Measure installed Laya; select thresholds on calibration only, freeze for holdout."""
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.language.laya_intent import hint_eligible, intent_request


def summary(rows, threshold, margin):
    accepted = [r for r in rows if hint_eligible(r['text']) and r['predicted'] != 'lainnya' and r['probability'] >= threshold and r['margin'] >= margin]
    correct = sum(r['predicted'] == r['expected'] for r in accepted)
    return {'samples': len(rows), 'raw_correct': sum(r['predicted'] == r['expected'] for r in rows),
        'accepted': len(accepted), 'accepted_correct': correct,
        'accepted_precision': correct / len(accepted) if accepted else None,
        'accepted_errors': [r['id'] for r in accepted if r['predicted'] != r['expected']]}


def main():
    dataset_path = ROOT / 'tests/fixtures/laya-intents.json'
    samples = json.loads(dataset_path.read_text(encoding='utf-8'))
    rows = []
    reuse = '--reuse' in sys.argv
    if reuse:
        rows = json.loads((ROOT / 'artifacts/laya-integration/classifier-baseline.json').read_text(encoding='utf-8'))['rows']
    with httpx.Client(base_url='http://127.0.0.1:18765', timeout=10, trust_env=False) as client:
        for case in samples:
            if reuse:
                break
            request = intent_request(case['text'], case.get('context'))
            started = time.perf_counter()
            response = client.post('/v1/systemone', json=request)
            response.raise_for_status()
            body = response.json()
            answer = body['answers']['intent']
            scores = sorted(answer['probabilities'].values(), reverse=True)
            rows.append({**case, 'http': response.status_code, 'predicted': answer['choice'],
                'probability': answer['probabilities'][answer['choice']], 'margin': scores[0] - scores[1],
                'entropy_confidence': answer['confidence'], 'probabilities': answer['probabilities'],
                'latency_ms': (time.perf_counter() - started) * 1000, 'usage': body['usage']})
            if len(rows) % 8 == 0:
                print(f'Measured {len(rows)}/{len(samples)}', flush=True)
    calibration = [r for r in rows if r['split'] == 'calibration']
    holdout = [r for r in rows if r['split'] == 'holdout']
    candidates = []
    for probability in (.5, .6, .65, .7, .75, .8, .85, .9, .93, .95, .97, .98, .99, .995, 1.0):
        for margin in (.1, .2, .3, .4, .5, .6, .7, .8, .9):
            measured = summary(calibration, probability, margin)
            if measured['accepted'] >= 10 and measured['accepted_precision'] == 1.0:
                candidates.append((measured['accepted'], probability, margin))
    selected = max(candidates, key=lambda item: (item[0], -item[1], -item[2])) if candidates else None
    probability, margin = selected[1:] if selected else (1.0, 1.0)
    report = {'dataset_sha256': hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        'selection_rule': 'After conservative eligibility gate, calibration only: >=10 accepted, zero accepted errors; maximize coverage. Original holdout was inspected during diagnosis: exploratory, not independent validation.',
        'threshold_found': bool(selected), 'min_probability': probability, 'min_margin': margin,
        'calibration': summary(calibration, probability, margin), 'holdout': summary(holdout, probability, margin),
        'latency_ms': {'median': statistics.median(r['latency_ms'] for r in rows),
            'p95': sorted(r['latency_ms'] for r in rows)[int(.95 * (len(rows) - 1))],
            'max': max(r['latency_ms'] for r in rows)},
        'rows': rows}
    out = ROOT / 'artifacts/laya-integration/classifier-comparison.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
