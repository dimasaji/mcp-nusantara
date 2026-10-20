"""Prepare the current operator documentation task; no provider, ingestion or approval."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.developer_core.controlled_write import ExecutionPaths, prepare_normal_plan


def main():
    source = 'docs/operational/NUSANTARA-V1-OPERATOR.md'
    target = 'docs/operational/published/NUSANTARA-V1-OPERATOR.md'
    if (ROOT / target).exists():
        raise SystemExit('Target sudah ada: siapkan pekerjaan baru setelah meninjau History; tidak ditimpa otomatis.')
    context = prepare_normal_plan(ExecutionPaths.for_root(ROOT),
        objective='Publikasikan panduan teknis operator Nusantara V1 yang telah diuji dan ditinjau.',
        expected_change='Membuat satu salinan panduan pada docs/operational/published. Tidak menjalankan shell, mengubah SOP asli, database, atau indeks.',
        documents={target: (ROOT / source).read_text(encoding='utf-8')},
        risk='LOW: satu file dokumentasi baru. Risiko isi panduan tidak sesuai kebutuhan operator; tinjau sebelum PASS.',
        tests_required=['test_normal_plan_prepares_without_human_approval', 'test_normal_plan_requires_complete_context_and_safe_targets',
                        'tests/test_v1_review_execution_api.py', 'control-plane/e2e/review-execution.spec.ts'],
        rollback='Periksa History dan perubahan pengguna; pindahkan hanya file panduan baru ke arsip. Sumber panduan tetap tersedia. Jangan hapus database atau indeks.')
    spec_path = ROOT / 'control-plane/evidence-requirements.json'
    spec = json.loads(spec_path.read_text())
    criterion = next(c for c in spec['criteria'] if c['id'] == 'AC10')
    required = ['app/developer_core/controlled_write.py', 'tests/test_normal_plan.py', source,
                'scripts/prepare_v1_operator_plan.py', 'data/developer_core/change_plan.json',
                '.developer_staging/' + context['change_id'] + '/' + target]
    for item in required:
        if item not in criterion['sources']: criterion['sources'].append(item)
    for name in ['test_normal_plan_prepares_without_human_approval', 'test_normal_plan_requires_complete_context_and_safe_targets']:
        if name not in criterion['tests']: criterion['tests'].append(name)
    spec_path.write_text(json.dumps(spec, indent=2) + '\n')
    print(json.dumps({'change_id': context['change_id'], 'plan_binding': context['plan_binding'],
                      'approval': 'REQUIRES_HUMAN_DECISION', 'target': target}))


if __name__ == '__main__': main()
