import json, time, statistics
from app.knowledge.engine import KnowledgeEngine

engine = KnowledgeEngine()
dataset = json.load(open('reports/search_eval_dataset.json', encoding='utf-8'))

recalls, mrrs, precisions, precisions_at_1, exacts, latencies = [], [], [], [], [], []
details = []
for item in dataset:
    q = item['query']
    expected = set(item['expected'])
    t0 = time.perf_counter()
    try:
        res = engine.search_knowledge(q, top_k=10)
    except Exception as e:
        res = []
        err = str(e)
    else:
        err = None
    lat = (time.perf_counter() - t0) * 1000.0
    latencies.append(lat)
    ids = [getattr(r, 'document_id', None) for r in (res or [])]
    top5 = ids[:5]
    top10 = ids[:10]
    # Recall@5
    if expected:
        recall = len(set(top5) & expected) / len(expected)
    else:
        recall = 1.0 if not top5 else 0.0
    recalls.append(recall)
    # MRR@10
    mrr = 0.0
    for rank, did in enumerate(top10, 1):
        if did in expected:
            mrr = 1.0 / rank
            break
    mrrs.append(mrr)
    # Precision@1 (primary metric)
    if top10:
        prec1 = 1.0 if top10[0] in expected else 0.0
    else:
        prec1 = 1.0 if not expected else 0.0
    precisions_at_1.append(prec1)
    # Precision@5
    if top5:
        prec = len(set(top5) & expected) / len(top5)
    else:
        prec = 1.0 if not expected else 0.0
    precisions.append(prec)
    # Exact-match: top-1 equals a single expected (or empty for no-result)
    if expected:
        exact = 1.0 if (top10 and top10[0] in expected) else 0.0
    else:
        exact = 1.0 if not top10 else 0.0
    exacts.append(exact)
    details.append({'query': q, 'type': item['type'], 'expected': sorted(expected),
                    'returned': ids, 'recall@5': round(recall,3), 'mrr@10': round(mrr,3),
                    'precision@5': round(prec,3), 'exact': exact, 'latency_ms': round(lat,1),
                    'error': err})

n = len(dataset)
report = {
    'num_queries': n,
    'Recall@5': round(sum(recalls)/n, 4),
    'MRR@10': round(sum(mrrs)/n, 4),
    'Precision@1': round(sum(precisions_at_1)/n, 4),
    'Precision@5': round(sum(precisions)/n, 4),
    'Exact_match_accuracy': round(sum(exacts)/n, 4),
    'Latency_ms_mean': round(statistics.mean(latencies), 1),
    'Latency_ms_median': round(statistics.median(latencies), 1),
    'Latency_ms_p95': round(sorted(latencies)[int(0.95*n)-1], 1),
    'details': details,
}
json.dump(report, open('reports/search_eval_report.json','w',encoding='utf-8'), indent=2, ensure_ascii=False)
print('Queries:', n)
print('Recall@5:', report['Recall@5'])
print('MRR@10:', report['MRR@10'])
print('Precision@1:', report['Precision@1'])
print('Precision@5:', report['Precision@5'])
print('Exact_match_accuracy:', report['Exact_match_accuracy'])
print('Latency mean/median/p95 ms:', report['Latency_ms_mean'], report['Latency_ms_median'], report['Latency_ms_p95'])
