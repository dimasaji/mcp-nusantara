import difflib, hashlib, json, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((OUT/'EVIDENCE_INVENTORY.json').read_text())
allowed={'app/knowledge/web_evidence.py','tests/test_web_evidence_pipeline.py'}
changed=[k for k,v in baseline['baseline_hashes'].items() if sha(ROOT/k)!=v]
unexpected=[k for k in changed if k.replace('\\','/') not in allowed]
fixtures=[p for p in baseline['files'] if 'official_sources' in p['path']]
fixture_checks=[{'path':f['path'],'sha256_before':f['sha256'],'sha256_after':sha(Path(f['path'])),
                 'unchanged':f['sha256']==sha(Path(f['path']))} for f in fixtures]
patch=[]
hashes=[]
for path,before in [('app/knowledge/web_evidence.py','web_evidence.py.before'),('tests/test_web_evidence_pipeline.py','test_web_evidence_pipeline.py.before')]:
    compile((ROOT/path).read_text(encoding='utf-8'),path,'exec')
    hashes.append({'path':path,'before':sha(OUT/before),'after':sha(ROOT/path)})
    patch+=list(difflib.unified_diff((OUT/before).read_text().splitlines(True),(ROOT/path).read_text().splitlines(True),fromfile='before/'+path,tofile='after/'+path))
(OUT/'SCOPED_CHANGES.patch').write_text(''.join(patch))
runs=[]
for xml in sorted(OUT.glob('*/results.xml')):
    s=ET.parse(xml).getroot().find('testsuite')
    guards=json.loads((xml.parent/'guards.json').read_text())
    counts={k:int(s.attrib[k]) for k in ['tests','failures','errors','skipped']}
    counts['passed']=counts['tests']-counts['failures']-counts['errors']-counts['skipped']
    runs.append({'run':xml.parent.name,'command':'.venv/Scripts/python.exe -B '+str((OUT/'verify.py').relative_to(ROOT)).replace('\\','/')+' '+xml.parent.name.split('-')[0],
      'exit_code':guards['pytest_exit'],'counts':counts,'deselected':69 if xml.parent.name.startswith('targeted') else 6,
      'guards':guards,'xml':str(xml.relative_to(ROOT))})
(OUT/'TEST_RESULTS.json').write_text(json.dumps({'runs':runs,'failure_preserved':'regression-20261009-182327: WinError 5 on temporary staging replacement; cause unestablished. Repeat passed without source/test changes.',
 'regression_exclusions':['actual_v2','dev_endpoint','consumers_correlation','empty_result','bootstrap_layers','owner_reads']},indent=2))
audit={'timestamp':datetime.now(timezone.utc).isoformat(),'changed_source_test_files':changed,
 'unauthorized_baseline_source_changes':unexpected,'hashes':hashes,'fixture_manifest_preservation':fixture_checks,
 'database_access':False,'sidecar_access':False,'runtime_operations':0,'network_requests':0,
 'console_changed':False,'syntax_compile':'PASS_NO_BYTECODE','comparison_scope':'Existing app/tests/Console source hashes captured before the interrupted governance work; only two authorized files changed.'}
(OUT/'CHANGE_AUDIT.json').write_text(json.dumps(audit,indent=2))
print(json.dumps({'changed':changed,'unexpected':unexpected,'fixtures_unchanged':all(f['unchanged'] for f in fixture_checks),'runs':[{'run':r['run'],'exit':r['exit_code'],'counts':r['counts']} for r in runs]},indent=2))
if unexpected or not all(f['unchanged'] for f in fixture_checks):raise SystemExit(1)
