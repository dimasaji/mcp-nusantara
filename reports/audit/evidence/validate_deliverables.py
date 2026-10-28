"""Validate report links/numerators and seal key evidence hashes; no product edits."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'reports/audit'
E=OUT/'evidence'
reports=['PRD_COMPLIANCE_MATRIX.md','GIT_HISTORY_AUDIT.md','ARCHITECTURE_AUDIT.md',
         'END_TO_END_TEST_REPORT.md','ROOT_CAUSE_ANALYSIS.md','TECHNICAL_DEBT_REGISTER.md',
         'REMEDIATION_PLAN.md','EXECUTIVE_AUDIT_SUMMARY.md']
errors=[]
for name in reports:
    path=OUT/name
    if not path.is_file() or path.stat().st_size<500:
        errors.append('missing_or_short:'+name); continue
    content=path.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)',content):
        if not target.startswith(('http:','https:','#')) and not (path.parent/target.split('#')[0]).exists():
            errors.append('broken_link:'+name+':'+target)
matrix=(OUT/reports[0]).read_text(encoding='utf-8')
rows=re.findall(r'^\| \*\*(FR-\d{2})\*\* .*?\| \*\*(PASS|FAIL|HOLD|NOT TESTED)\*\*',matrix,re.M)
assert len(rows)==15 and len({r[0] for r in rows})==15, rows
assert sum(s=='PASS' for _,s in rows)==3
assert sum(s=='FAIL' for _,s in rows)==6
assert sum(s=='HOLD' for _,s in rows)==6
summary=json.loads((E/'backend-verified-summary.json').read_text())
assert summary['counts']=={'error':47,'GUARD':85,'failure':44,'OTHER':6,'passed':1040,'skipped':21},summary['counts']
probes=json.loads((E/'reproductions-final/probe-results.json').read_text())
assert len(probes['probes'])==4 and all(p['verdict']=='FAIL' for p in probes['probes'])
assert probes['probes'][0]['document_title']=='PERMOHONAN DATA PRIBADI'
assert json.loads((E/'docling-native-final/native-result.json').read_text())['status']=='COMPLETE'
assert not json.loads((E/'audit-integrity-summary.json').read_text())['source_drift_since_baseline']
keys=reports+['evidence/'+n for n in ['COMMANDS.md','git_baseline.json','source_inventory.json',
 'prd-baseline.json','prd-baseline-text.txt','audit-integrity-summary.json','backend-verified-summary.json',
 'backend-verified/junit.xml','backend-verified-console.txt','runner-verified-snapshot.py',
 'frontend-results.json','frontend-recheck.json','browser-results.json','browser-console.txt','typescript.txt',
 'docling-native-final/native-result.json','docling-native-final/extraction.json',
 'reproductions-final/probe-results.json','reproductions/reopen-results.json',
 'runtime-probe-final.json','run_guarded_tests.py','reproduce_findings.py',
 'standards_findings.md','spec_findings.md','write_reports.py','validate_deliverables.py']]
manifest={'contract':'NCP-V1-FULL-PRD-AUDIT-001/002','created_at_utc':datetime.now(timezone.utc).isoformat(),
          'readiness':'HOLD','source_changed':False,'database_operational_write_authorized':False,
          'operator_baseline_accepted':True,'operational_approval_created':False,
          'scope':'key deliverables/evidence only; caches/temp fixture trees excluded',
          'validation_errors':errors,'sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in keys}}
(OUT/'AUDIT_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'reports':len(reports),'matrix':dict((s,sum(status==s for _,status in rows)) for s in ['PASS','FAIL','HOLD']),
                  'hashed_artifacts':len(keys),'validation_errors':errors}))
raise SystemExit(1 if errors else 0)
