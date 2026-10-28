"""Read-only evidence analysis. Writes only new audit summaries."""
import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
inventory = json.loads((OUT/'source_inventory.json').read_text())
drift=[]
for item in inventory['files']:
    path=ROOT/item['path']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        drift.append(item['path'])
fixture=json.loads((ROOT/'tests/fixtures/v1-current-contract/source-contract.json').read_text(encoding='utf-8-sig'))
pins=[]
for name, expected in fixture.get('current_sources',{}).items():
    path=ROOT/name
    actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    pins.append({'path':name,'expected':expected,'actual':actual,'matches':actual==expected})
historical=[]
for name in ['artifacts/document-chat-20261023/tests.xml','artifacts/v1-execution/regression-final.xml',
             'artifacts/docling-ui/answers.json','artifacts/docling-main-chat/answers.json']:
    path=ROOT/name
    if not path.is_file():
        historical.append({'path':name,'exists':False});continue
    item={'path':name,'exists':True,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'provenance':'historical artifact; not current runtime evidence'}
    if path.suffix=='.xml':
        try:
            root=ET.parse(path)
            cases=list(root.iter('testcase'))
            item.update(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),
                        errors=sum(c.find('error') is not None for c in cases),
                        skipped=sum(c.find('skipped') is not None for c in cases))
        except ET.ParseError:item['parse_error']=True
    else:
        value=json.loads(path.read_text(encoding='utf-8-sig'))
        item['saved_answer_entries']=len(value) if isinstance(value,list) else None
    historical.append(item)
routes=[]
for path in (ROOT/'app').rglob('*.py'):
    tree=ast.parse(path.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator,ast.Call) and isinstance(decorator.func,ast.Attribute) and decorator.func.attr in {'get','post','put','patch','delete'}:
                    route=decorator.args[0].value if decorator.args and isinstance(decorator.args[0],ast.Constant) else 'dynamic'
                    routes.append({'file':path.relative_to(ROOT).as_posix(),'line':node.lineno,'method':decorator.func.attr.upper(),'route':route})
summary={'source_drift_since_baseline':drift,'files_rechecked':len(inventory['files']),
         'current_source_pins':pins,'historical_evidence':historical,
         'graph_bytes':(ROOT/'graphify-out/graph.json').stat().st_size,
         'graph_consumer_byte_limit':16*1024*1024,'routes':routes,
         'route_warning':'static decorators include optional/experimental/backup files; not installed-route proof'}
(OUT/'audit-integrity-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
if (OUT/'backend-verified/junit.xml').is_file():
    testroot=ET.parse(OUT/'backend-verified/junit.xml')
    counts=Counter()
    modules=defaultdict(Counter)
    details=[]
    for test in testroot.iter('testcase'):
        nodes=[(k,test.find(k)) for k in ('failure','error','skipped') if test.find(k) is not None]
        status=nodes[0][0] if nodes else 'passed'
        counts[status]+=1
        modules[test.get('classname','')][status]+=1
        for kind,node in nodes:
            if kind=='skipped':continue
            message=node.get('message','')
            category='GUARD' if 'AUDIT_GUARD_BLOCKED' in message+(node.text or '') else 'OTHER'
            counts[category]+=1
            details.append({'module':test.get('classname'),'test':test.get('name'),
                            'kind':kind,'category':category,'message':message[:1700]})
    (OUT/'backend-verified-summary.json').write_text(json.dumps({
        'counts':dict(counts),'modules':{k:dict(v) for k,v in modules.items()},
        'failures':details},indent=2),encoding='utf-8')
print(json.dumps({'source_drift':drift,'source_pin_mismatches':[p['path'] for p in pins if not p['matches']],
                  'historical':historical,'route_decorators':len(routes)},indent=2))
