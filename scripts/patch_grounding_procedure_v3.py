"""Read-only frontend observation for master-contract forensic audit.

GET endpoints only; no chat, no writes to services. Admin token read from
.env and used solely as a request header, never printed. Responses are
status metadata; saved locally as audit evidence.
"""
import json
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TOKEN = next(l.strip().split('=', 1)[1]
             for l in (PROJECT / '.env').read_text(encoding='utf-8').splitlines()
             if l.startswith('NUSANTARA_ADMIN_TOKEN='))
BASE = 'http://127.0.0.1:8000/v1/frontend/'
OUT = PROJECT / 'reports' / 'master-001'


def get(ep):
    req = urllib.request.Request(BASE + ep, headers={'x-admin-token': TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as exc:
        return {'error': f'{type(exc).__name__}: {exc}'}


def main():
    evidence = {}
    for ep in ('snapshot', 'model-status', 'knowledge-status',
               'operations-summary', 'hermes/connection', 'history'):
        evidence[ep] = get(ep)
    (OUT / 'control_plane_observation.json').write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding='utf-8')

    snap = evidence['snapshot']
    print('SNAPSHOT status:', snap.get('status'))
    for p in snap.get('phases', []):
        print(p['id'], '|', p['name'][:46], '|', p['status'], '|', p.get('kind'))
    ms = evidence['model-status']
    print('MODEL:', ms.get('provider'), ms.get('model'), ms.get('status'))
    ks = evidence['knowledge-status']
    print('KNOWLEDGE keys:', sorted(ks.keys())[:12])
    print('KNOWLEDGE summary:', json.dumps(
        {k: ks[k] for k in list(ks)[:6]}, ensure_ascii=False)[:300])
    hc = evidence['hermes/connection']
    print('HERMES:', json.dumps(hc, ensure_ascii=False)[:250])
    ops = evidence['operations-summary']
    print('OPS:', json.dumps(ops, ensure_ascii=False)[:250])
    print('SAVED', OUT / 'control_plane_observation.json')


if __name__ == '__main__':
    main()